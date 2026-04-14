# CLAUDE.md

## What is this project?

A TypeScript-to-Python translation tool (`tt`) for the Oslo Enhanced Hackathon 2026. The tool translates part of [ghostfolio](https://github.com/ghostfolio/ghostfolio) (a financial portfolio management system) from TypeScript to Python. The translated Python code is tested against an API test suite.

**Scoring:** 85% test pass rate, 15% code quality (via pyscn). Judge review adjusts final score.

## Competition Rules (must not violate)

1. **No LLMs in the translation pipeline.** LLMs may help build the TT itself.
2. **No project-specific logic in `tt/`** (Rule 9). No hardcoded `@ghostfolio/...` import paths. Project config belongs in `tt_import_map.json` inside the scaffold directory.
3. **No calling node/js-tools** (Rule 6). The translation must happen in Python.
4. **Wrapper is immutable.** `app/main.py` and `app/wrapper/` must be byte-for-byte identical to the example.
5. **TT generates only `app/implementation/`.** Nothing outside that directory may be generated or modified.
6. **Frequent commits.** Git log should reflect gradual development.
7. Run `make detect_rule_breaches` before publishing to catch violations.

## Key Commands

```bash
# Translate
uv run --project tt tt translate

# Test the translation
make spinup-and-test-ghostfolio_pytx

# Translate + test in one step
make translate-and-test-ghostfolio_pytx

# Full evaluation (tests + code quality)
make evaluate_tt_ghostfolio

# Check for rule violations
make detect_rule_breaches

# Publish results to live dashboard
make publish_results
```

## Project Layout

```
tt/tt/                          # Translation tool source (what we build)
  __main__.py                   # Entry: python -m tt
  cli.py                        # CLI: arg parsing, scaffold setup, runs translator
  translator.py                 # Translation logic
  scaffold/ghostfolio_pytx/     # Support modules overlaid onto output

translations/
  ghostfolio_pytx/              # Output of `tt translate` (generated)
    app/
      main.py                   # Immutable wrapper (DO NOT MODIFY)
      wrapper/                  # Immutable wrapper layer (DO NOT MODIFY)
      implementation/           # TT-generated code (ONLY modify this)
        portfolio/calculator/roai/portfolio_calculator.py

  ghostfolio_pytx_example/      # Reference skeleton (immutable source)

projects/ghostfolio/            # Original TypeScript source
  apps/api/src/app/portfolio/
    calculator/
      portfolio-calculator.ts   # Base class (~1,173 lines)
      roai/portfolio-calculator.ts  # ROAI subclass (~1,009 lines)

projecttests/ghostfolio_api/    # API integration test suite (139 tests)
evaluate/                       # Scoring and rule breach detection
make/                           # Makefile includes (evalsolution.mk, etc.)
helptools/                      # Scaffold setup script
```

## Translation Pipeline

1. `cli.py` parses args, runs `helptools/setup_ghostfolio_scaffold_for_tt.py` to copy the immutable wrapper
2. Scaffold overlays support modules from `tt/tt/scaffold/ghostfolio_pytx/`
3. `translator.py` reads TS source, transforms it, writes to `app/implementation/`

## What Needs Translating

The real target is narrow: `RoaiPortfolioCalculator` and its dependencies.

**Two TS files:**
- Base class (`portfolio-calculator.ts`): `computeSnapshot()`, chart date generation, transaction point aggregation
- ROAI subclass (`roai/portfolio-calculator.ts`): `getSymbolMetrics()` (~350 lines, the core arithmetic engine)

**Required calculator methods (from the abstract interface):**
- `get_performance()` -> `{chart, firstOrderDate, performance: {...}}`
- `get_investments(group_by)` -> `{investments: [{date, investment}]}`
- `get_holdings()` -> `{holdings: {symbol: {...}}}`
- `get_details(base_currency)` -> `{accounts, holdings, summary, ...}`
- `get_dividends(group_by)` -> `{dividends: [{date, investment}]}`
- `evaluate_report()` -> `{xRay: {categories, statistics}}`

## Dominant TS Patterns in Source

These patterns account for ~90% of the source by line count:

| Pattern | Frequency | Python Equivalent |
|---------|-----------|-------------------|
| `new Big(x)` / `.plus()` / `.minus()` / `.mul()` / `.div()` | ~200+ | `Decimal` operators |
| `x ?? y` (nullish coalescing) | 30+ | `x if x is not None else y` |
| `x?.y` (optional chaining) | 15+ | `.get()` / None checks |
| `.filter()` / `.map()` | 27+ | List comprehensions |
| date-fns (`format`, `isBefore`, `differenceInDays`) | ~20 | `datetime` / `timedelta` |
| lodash (`sortBy`, `cloneDeep`) | ~10 | `sorted()`, `deepcopy()` |
| `this.` | everywhere | `self.` |

## Test Leverage (implementation priority)

| Priority | Target | Tests Unlocked |
|----------|--------|---------------|
| 1 | `get_performance()` core (cost basis, realized P&L) | ~55 |
| 2 | Market price integration (unrealized P&L) | ~20 |
| 3 | TWI denominator (closed position percentages) | ~15 |
| 4 | Investment timeline with grouping | ~30 |
| 5 | Chart data, dividends, report | ~20 |

Baseline without translation: 48 passed, 87 failed (135 total).

## Python Environment

- Python >= 3.11 (uses 3.14 in .venv)
- Package manager: `uv`
- Run TT: `uv run --project tt tt translate`
- TT dependencies in `tt/pyproject.toml`
- Translation output dependencies in `translations/ghostfolio_pytx/pyproject.toml`
