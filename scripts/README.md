# Autoresearch Loop Scripts

Three scripts that instrument the iteration loop. All metrics are stored locally in `results.tsv` (gitignored) and per-run logs in `runs/`.

## Usage

### 1. Run an experiment

```bash
bash scripts/evaluate.sh "description of what you changed"
```

This runs the full translate+test cycle and appends a row to `results.tsv`. It prints:
- Pass/fail/error counts
- Delta from previous best
- New passes (tests that flipped green)
- Regressions (tests that flipped red)
- Suggested status (KEEP/DISCARD)

### 2. Mark the result

```bash
bash scripts/mark.sh keep      # improvement, advance branch
bash scripts/mark.sh discard   # regression or no improvement
bash scripts/mark.sh baseline  # first run, establishes the baseline
bash scripts/mark.sh crash     # server failed to start
```

Updates the status column of the last row in `results.tsv`.

### 3. View stats

```bash
bash scripts/stats.sh              # full summary with improvement timeline
bash scripts/stats.sh --last 10    # last 10 experiments
bash scripts/stats.sh --keeps      # only kept experiments
bash scripts/stats.sh --csv        # raw TSV for piping to other tools
```

## Data Format

`results.tsv` is tab-separated with these columns:

| Column | Description |
|---|---|
| timestamp | UTC ISO-8601 |
| commit | 7-char git hash |
| pass | Tests passing |
| fail | Tests failing |
| error | Tests erroring |
| new_passes | Tests flipped green since last run |
| new_failures | Tests flipped red since last run (regressions) |
| duration_s | Total cycle time in seconds |
| status | baseline / keep / discard / crash / pending |
| description | What was changed |

## Per-run logs

Full pytest output for each run is saved to `runs/run_TIMESTAMP.log`. These are useful for debugging specific test failures after the fact.

## Integration with the agent loop

The agent (Claude Code) uses these scripts in the PROGRAM.md loop:

```
1. bash scripts/evaluate.sh "added Big.js .plus() transform"
2. Read the printed summary
3. If KEEP: bash scripts/mark.sh keep
   If DISCARD: bash scripts/mark.sh discard && git reset --hard HEAD~1
4. bash scripts/stats.sh (every ~5 experiments)
5. Loop
```
