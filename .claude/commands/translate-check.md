Run the full translate-and-test loop, then analyze results.

## Steps

1. Run `make translate-and-test-ghostfolio_pytx` and capture the full output
2. Parse the pytest output to extract:
   - Total passed / failed / error counts
   - List of each failed test name and its one-line failure reason
   - List of each passed test name
3. Compare against the baseline (48 passed / 87 failed from scaffold alone)
4. Group failures by endpoint:
   - `get_performance` (chart tests)
   - `get_holdings`
   - `get_investments`
   - `get_details`
   - `get_dividends`
   - `evaluate_report`
5. For each failure group, identify the most common assertion failure pattern (e.g., "expected 50098.3 got 0", "key not found in chart")
6. Recommend which calculator method to focus on next based on which would unlock the most tests

## Output format

```
RESULTS: X passed / Y failed (delta: +N / -M from baseline 48/87)

FAILURES BY ENDPOINT:
  get_performance (chart): N failures - [common pattern]
  get_holdings: N failures - [common pattern]
  ...

NEXT TARGET: [method name] - would unlock ~N tests
```

Keep the output concise. Focus on actionable next steps, not a wall of test output.
