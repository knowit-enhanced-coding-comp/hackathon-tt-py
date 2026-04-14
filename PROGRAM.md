# PROGRAM.md -- Agent Research Protocol

This is the control document for the autoresearch loop. It tells the agent how to iterate on the translator. The agent follows this protocol; the human writes and refines it.

Read PRIORITIZATION.md before starting. It defines P0-P4 priorities and the transform build order.

## Constraints

- You may ONLY edit files under `tt/tt/`
- You may NOT edit files under `projecttests/`, `translations/ghostfolio_pytx_example/`, or `evaluate/`
- You may NOT use LLMs for the actual translation (Rule 1)
- You may NOT put project-specific logic in `tt/tt/` (Rule 9). Use `tt_import_map.json` in the scaffold for project mappings.
- The wrapper layer (`app/main.py` + `app/wrapper/`) must remain byte-for-byte identical to the example (Rule 9/10)
- You may add files to `tt/tt/scaffold/ghostfolio_pytx/` for support modules that get copied into the output

## The Loop

Never stop. Never ask the human. Run indefinitely until manually interrupted.

### Phase 1: OBSERVE

Run `/translate-check` to get the current state.

This gives you:
- Pass/fail counts and delta from baseline (48/87)
- Failures grouped by endpoint
- The most common assertion failure pattern per group
- A recommendation for which method to target next

If this is the first run, also run `/rule-check` to verify you start from a clean state.

### Phase 2: ORIENT

Pick the highest-leverage target. Follow the priority order from PRIORITIZATION.md:

```
P0: Big.js transforms     (blocks everything)
P1: getSymbolMetrics()     (~50 tests, highest leverage)
P2: get_holdings/investments (~45 tests)
P3: get_details/dividends  (~30 tests)
P4: evaluate_report        (~10 tests, lowest ROI)
```

Within each priority level, pick the specific failing test that would be easiest to fix. Read the test file to understand what value it expects. Trace back to the TypeScript source.

Use `/ts-pattern-lookup [pattern]` to get the correct Python equivalent for any TS construct you encounter.

Use `/diff-ts-py [method]` to see what the current translation produces versus what the TS source contains.

### Phase 3: MUTATE

Make ONE focused change to the translator. Examples:
- Add a new transform pass (e.g., `tt/tt/transforms/big_js.py`)
- Fix a pattern match in an existing transform
- Add a support module to the scaffold
- Fix the emitter logic

Keep changes small and focused. One transform per experiment. If a change touches more than ~50 lines, break it into smaller steps.

Commit the change:
```bash
git add tt/tt/
git commit -m "experiment: [short description of what you changed]"
```

### Phase 4: EVALUATE

Run `/translate-check` again.

Extract the key metrics:
- `pass_count`: total tests passing
- `fail_count`: total tests failing
- `new_passes`: tests that flipped from fail to pass
- `new_failures`: tests that flipped from pass to fail (regressions)

### Phase 5: DECIDE

```
IF pass_count > previous_best:
    STATUS = KEEP
    Advance the branch (commit stays)

ELIF pass_count == previous_best AND new_failures == 0:
    IF change makes code simpler or more maintainable:
        STATUS = KEEP
    ELSE:
        STATUS = DISCARD
        git reset --hard HEAD~1

ELSE (pass_count < previous_best OR new_failures > 0):
    STATUS = DISCARD
    git reset --hard HEAD~1
```

### Phase 6: LOG

Append to `results.tsv` (create if it does not exist):

```
commit	pass	fail	new_passes	new_failures	status	description
```

Use tab separation. Include the 7-char git hash, counts, status (keep/discard/crash), and a short description of what was tried.

### Phase 7: VALIDATE (every 5 experiments)

Every 5th experiment, run these additional checks:

1. `/rule-check` -- ensure no rule violations have crept in
2. `/score-estimate` -- get the full competition score (tests + code quality)

If rule violations are found, fix them immediately (this counts as the next experiment).

If code quality score is dropping, consider a cleanup experiment (refactor translated output for readability).

### Phase 8: LOOP

Go back to Phase 1. Never stop.

## Strategy Hints

### What to try first (in order)

1. **Get tree-sitter parsing working.** The current regex translator is a toy. Replace it with tree-sitter-typescript. This is infrastructure, not a scoring improvement, but everything depends on it.

2. **Big.js arithmetic.** This is P0 from PRIORITIZATION.md. Every line of the calculator uses Big.js. The single transform `new Big(x).plus(y)` -> `Decimal(x) + y` and its variants will unlock the most tests.

3. **Class structure.** `export class RoaiPortfolioCalculator extends PortfolioCalculator` -> `class RoaiPortfolioCalculator(PortfolioCalculator):` with `self` parameter injection.

4. **The getSymbolMetrics main loop.** This is a ~350-line method that iterates over orders by date, tracking running totals of investment, fees, dividends, performance. Getting this loop structure right is P1.

5. **Date handling.** `format(date, DATE_FORMAT)`, `differenceInDays`, `isBefore`, `eachYearOfInterval`. Required for chart date generation.

6. **Chart date map generation.** The base class `getChartDateMap()` samples dates at regular intervals plus year boundaries. Tests assert specific dates (2021-12-31, 2022-01-01). This needs correct translation.

### What to try when stuck

- Read the specific failing test assertion. It tells you the expected value.
- Run `/diff-ts-py [method]` to see what the translator currently produces.
- Run `/ts-pattern-lookup [pattern]` for any unfamiliar TS construct.
- Look at `results.tsv` for patterns: which categories of changes improve test count?
- Try a different approach to the same problem rather than iterating on a broken one.
- If a transform is producing wrong values, add a simpler test case first (test_btcusd.py is the simplest: 1 BUY, known prices).

### What NOT to try

- General-purpose TS features that do not appear in the ROAI source
- Formatting or style improvements (black handles this, and it is only 15% of score)
- `evaluate_report()` before P0-P2 are solid
- Comment preservation
- Multi-file changes in a single experiment (keep diffs small)

## Skill Reference

These Claude Code skills are available during the loop:

| Skill | When to use |
|---|---|
| `/translate-check` | Every experiment. Run translate+test, parse results, show delta from baseline, recommend next target. |
| `/rule-check` | Every 5 experiments. Detect rule violations before they accumulate. |
| `/score-estimate` | Every 5 experiments. Full competition score (85% tests + 15% quality). |
| `/ts-pattern-lookup [pattern]` | When you encounter an unfamiliar TS construct. Provides Python equivalent + gotchas. |
| `/diff-ts-py [method]` | When diagnosing a failing test. Shows TS source vs Python output side-by-side with annotations. |
| `/explain-tt-strategy` | After major changes. Verifies you can articulate what the translator does (needed for judge presentation). |

## Success Criteria

| Milestone | Tests | Action |
|---|---|---|
| Scaffold baseline | 48/135 | Starting point |
| P0 done | 55-60/135 | Big.js transforms working, basic arithmetic translates |
| P1 done | 95-100/135 | getSymbolMetrics produces correct chart data |
| P2 done | 115-120/135 | Holdings and investments assemble correctly |
| P3 done | 125-130/135 | Details and dividends work |
| P4 done | 130-135/135 | Report evaluation (stretch goal) |
| Competition-ready | 120+/135 | Rule-compliant, clean code quality, explainable |

## Failure Modes to Watch For

1. **Regression spiral**: A new transform breaks previously passing tests. The keep/discard ratchet prevents this, but watch for it. If you discard 3 experiments in a row on the same problem, step back and rethink the approach.

2. **Rule violation creep**: As the translator gets more complex, it is easy to accidentally add project-specific logic to `tt/tt/`. Run `/rule-check` regularly.

3. **Wrapper modification**: The scaffold setup must copy wrapper files byte-for-byte. If tests fail on endpoint routing (404s, 500s on basic endpoints), the wrapper may be corrupted. Diff against example.

4. **Floating point drift**: Use `Decimal` everywhere in the calculator, not `float`. Tests assert with `rel=1e-4` tolerance, but accumulated float errors can exceed this.

5. **Date off-by-one**: The TS code uses `isBefore(date, endDate)` (exclusive) vs `<=` (inclusive). Getting this wrong shifts chart entries by one day.

## Meta-Loop (after 20+ experiments)

After 20 experiments, review `results.tsv` and analyze:

1. **What categories of transforms improved test count?** Double down on what works.
2. **What categories were consistently discarded?** Stop trying those.
3. **Are there clusters of failing tests with the same root cause?** Attack the root cause, not individual tests.
4. **Is the code quality score trending down?** Schedule a cleanup experiment.

Update the "Strategy Hints" section of this file based on what you learn. This is the outer loop: improving the research protocol itself based on accumulated evidence.
