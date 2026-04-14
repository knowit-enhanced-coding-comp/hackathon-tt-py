Compute the current projected competition score.

## Steps

1. Run `make scoring` and capture the full output (this runs test scoring + code quality + overall)
2. Parse the three scoring components:
   - **Test score** (85% weight): count of passed tests out of total, weighted by difficulty
   - **Code quality score** (15% weight): pyscn metrics (health, complexity, dead code, duplication, coupling, dependency, architecture)
   - **Overall score**: weighted combination
3. Read `evaluate/scoring/results/latest.json` if it exists for detailed breakdown
4. Compare against baseline (48/135 tests = scaffold-only score)
5. Identify the scoring leverage: which area (more tests vs better code quality) would yield the most points per hour of effort

## Output format

```
SCORE ESTIMATE
  Tests:   X/135 passed (Y%)     [85% weight] = Z points
  Quality: A/100                  [15% weight] = B points
  TOTAL:   T points (delta: +D from baseline)

BREAKDOWN:
  Test pass rate: X%
  Code quality: health=_, complexity=_, duplication=_, coupling=_

LEVERAGE:
  Next 10 tests = +X points
  Quality from C to D = +Y points
  Recommendation: [focus area]
```
