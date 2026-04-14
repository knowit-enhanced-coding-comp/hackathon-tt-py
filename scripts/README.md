# Autoresearch Loop Scripts

Three Python scripts that instrument the iteration loop. All metrics are stored locally in `results.csv` (gitignored) and per-run logs in `runs/`.

## Usage

### 1. Run an experiment

```bash
python scripts/evaluate.py "description of what you changed"
```

This runs the full translate+test cycle and appends a row to `results.csv`. It prints:
- Pass/fail/error counts
- Delta from previous best
- New passes (tests that flipped green)
- Regressions (tests that flipped red)
- Suggested status (KEEP/DISCARD)

### 2. Mark the result

```bash
python scripts/mark.py keep      # improvement, advance branch
python scripts/mark.py discard   # regression or no improvement
python scripts/mark.py baseline  # first run, establishes the baseline
python scripts/mark.py crash     # server failed to start
```

Updates the status column of the last row in `results.csv`.

### 3. View stats

```bash
python scripts/stats.py              # full summary with improvement timeline
python scripts/stats.py --last 10    # last 10 experiments
python scripts/stats.py --keeps      # only kept experiments
python scripts/stats.py --csv        # raw CSV for piping to other tools
```

## Data Format

`results.csv` columns:

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

Full pytest output for each run is saved to `runs/run_TIMESTAMP.log`. Useful for debugging specific failures after the fact.

## Integration with the agent loop

```
1. python scripts/evaluate.py "added Big.js .plus() transform"
2. Read the printed summary
3. If KEEP:    python scripts/mark.py keep
   If DISCARD: python scripts/mark.py discard && git reset --hard HEAD~1
4. python scripts/stats.py (every ~5 experiments)
5. Loop
```
