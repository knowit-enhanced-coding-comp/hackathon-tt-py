Show a side-by-side comparison of TypeScript source and Python translation output for a given method.

## Input

The user provides a method name (e.g., `getSymbolMetrics`, `calculateOverallPerformance`, `get_performance`) or "all" for a summary.

## Steps

1. Find the method in the TypeScript source:
   - Base class: `projects/ghostfolio/apps/api/src/app/portfolio/calculator/portfolio-calculator.ts`
   - ROAI subclass: `projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts`
2. Find the corresponding Python output:
   - `translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py`
   - If the translation output does not exist yet, run `uv run --project tt tt translate` first
3. Extract both methods
4. Present them side by side with annotations highlighting:
   - Big.js -> Decimal conversions
   - date-fns -> datetime conversions
   - lodash -> Python stdlib conversions
   - Structural changes (class syntax, method signatures, destructuring)
   - Any semantic differences or potential bugs

## Output format

```
=== TypeScript: methodName (roai/portfolio-calculator.ts:L42-L98) ===
[TS code]

=== Python: method_name (roai/portfolio_calculator.py:L30-L75) ===
[Python code]

=== Semantic annotations ===
- L45 TS: `new Big(0)` -> L32 PY: `Decimal(0)` [correct]
- L52 TS: `.plus()` -> L38 PY: `+` operator [correct]
- L60 TS: `format(date, DATE_FORMAT)` -> L44 PY: missing! [BUG: date not formatted]
...

=== Coverage: X/Y constructs correctly translated ===
```

If the user says "all", list all methods in both TS files with their translation status (translated / stub / missing).
