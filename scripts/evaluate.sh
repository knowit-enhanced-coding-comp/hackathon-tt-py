#!/usr/bin/env bash
# evaluate.sh — Run translate+test cycle and record metrics to results.tsv
#
# Usage:
#   bash scripts/evaluate.sh "description of what changed"
#
# What it does:
#   1. Kills any leftover server
#   2. Runs tt translate
#   3. Spins up the translated server and runs pytest
#   4. Parses pytest output for pass/fail counts and test names
#   5. Compares against previous best from results.tsv
#   6. Prints a summary with delta
#   7. Appends a row to results.tsv
#
# Output files:
#   results.tsv          — Cumulative experiment ledger (tab-separated)
#   runs/               — Per-run pytest output logs
#
# The caller (agent or human) decides keep/discard based on the printed summary.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_FILE="$ROOT_DIR/results.tsv"
RUNS_DIR="$ROOT_DIR/runs"
DESCRIPTION="${1:-no description}"

mkdir -p "$RUNS_DIR"

# --- Initialize results.tsv if missing ---
if [ ! -f "$RESULTS_FILE" ]; then
    printf "timestamp\tcommit\tpass\tfail\terror\tnew_passes\tnew_failures\tduration_s\tstatus\tdescription\n" > "$RESULTS_FILE"
fi

# --- Get current git state ---
COMMIT="$(git -C "$ROOT_DIR" rev-parse --short=7 HEAD 2>/dev/null || echo 'unknown')"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Get previous best pass count from results.tsv ---
PREV_BEST=0
if [ -f "$RESULTS_FILE" ] && [ "$(wc -l < "$RESULTS_FILE")" -gt 1 ]; then
    # Find the highest pass count among "keep" or "baseline" rows, or all rows if none kept yet
    PREV_BEST=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '{if($3+0 > max) max=$3+0} END {print max+0}')
fi

# --- Get previous test names for diff ---
PREV_PASS_FILE="$RUNS_DIR/.last_passed_tests"
PREV_FAIL_FILE="$RUNS_DIR/.last_failed_tests"

# --- Kill any leftover server ---
bash "$ROOT_DIR/projecttests/tools/kill_ghostfolio_pytx.sh" 2>/dev/null || true

# --- Run translate ---
echo "=== TRANSLATE ==="
TRANSLATE_START=$SECONDS
uv run --project "$ROOT_DIR/tt" tt translate 2>&1 | tail -5
TRANSLATE_TIME=$((SECONDS - TRANSLATE_START))
echo "  Translate took ${TRANSLATE_TIME}s"

# --- Run tests ---
echo ""
echo "=== TEST ==="
TEST_START=$SECONDS
RUN_LOG="$RUNS_DIR/run_${TIMESTAMP//:/-}.log"

# Sync deps quietly
uv sync --project "$ROOT_DIR/translations/ghostfolio_pytx" --extra dev --quiet 2>/dev/null || true

# Start server
PORT="${PYTX_PORT:-3335}"
(cd "$ROOT_DIR/translations/ghostfolio_pytx" && uv run python -m uvicorn app.main:app \
    --host 127.0.0.1 --port "$PORT" --log-level warning) &
SERVER_PID=$!

cleanup() {
    kill "$SERVER_PID" 2>/dev/null || true
    lsof -ti:"$PORT" 2>/dev/null | xargs kill 2>/dev/null || true
}
trap cleanup EXIT

# Wait for health
for i in $(seq 1 30); do
    if curl -sf "http://localhost:$PORT/api/v1/health" > /dev/null 2>&1; then
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Server did not start" >&2
        DURATION=$((SECONDS - TEST_START + TRANSLATE_TIME))
        printf "%s\t%s\t0\t0\t0\t0\t0\t%d\tcrash\t%s\n" "$TIMESTAMP" "$COMMIT" "$DURATION" "$DESCRIPTION" >> "$RESULTS_FILE"
        exit 1
    fi
    sleep 1
done

# Run pytest with verbose output, capture everything
GHOSTFOLIO_API_URL="http://localhost:$PORT" \
    uv run --project "$ROOT_DIR/tt" pytest "$ROOT_DIR/projecttests/ghostfolio_api" -v 2>&1 | tee "$RUN_LOG" || true

TEST_TIME=$((SECONDS - TEST_START))
DURATION=$((TRANSLATE_TIME + TEST_TIME))

# Kill server
cleanup
trap - EXIT

# --- Parse pytest output ---
PASS_COUNT=$(grep -cE "^projecttests/.*PASSED" "$RUN_LOG" 2>/dev/null || echo 0)
FAIL_COUNT=$(grep -cE "^projecttests/.*FAILED" "$RUN_LOG" 2>/dev/null || echo 0)
ERROR_COUNT=$(grep -cE "^projecttests/.*ERROR" "$RUN_LOG" 2>/dev/null || echo 0)

# Extract test names
CURRENT_PASS_FILE="$RUNS_DIR/.current_passed_tests"
CURRENT_FAIL_FILE="$RUNS_DIR/.current_failed_tests"
grep -E "^projecttests/.*PASSED" "$RUN_LOG" | awk '{print $1}' | sort > "$CURRENT_PASS_FILE" 2>/dev/null || touch "$CURRENT_PASS_FILE"
grep -E "^projecttests/.*FAILED" "$RUN_LOG" | awk '{print $1}' | sort > "$CURRENT_FAIL_FILE" 2>/dev/null || touch "$CURRENT_FAIL_FILE"

# Compute diffs
NEW_PASSES=0
NEW_FAILURES=0
NEW_PASSES_LIST=""
NEW_FAILURES_LIST=""

if [ -f "$PREV_PASS_FILE" ]; then
    NEW_PASSES_LIST=$(comm -23 "$CURRENT_PASS_FILE" "$PREV_PASS_FILE" 2>/dev/null || true)
    NEW_FAILURES_LIST=$(comm -23 "$PREV_FAIL_FILE" "$CURRENT_FAIL_FILE" 2>/dev/null | head -20 || true)
    # Wait, new failures = tests that WERE passing but now fail
    NEW_FAILURES_LIST=$(comm -23 "$PREV_PASS_FILE" "$CURRENT_PASS_FILE" 2>/dev/null || true)
    NEW_PASSES=$(echo "$NEW_PASSES_LIST" | grep -c . 2>/dev/null || echo 0)
    NEW_FAILURES=$(echo "$NEW_FAILURES_LIST" | grep -c . 2>/dev/null || echo 0)
fi

# Update last-known test lists
cp "$CURRENT_PASS_FILE" "$PREV_PASS_FILE" 2>/dev/null || true
cp "$CURRENT_FAIL_FILE" "$PREV_FAIL_FILE" 2>/dev/null || true

# --- Determine status suggestion ---
DELTA=$((PASS_COUNT - PREV_BEST))
if [ "$PASS_COUNT" -gt "$PREV_BEST" ] && [ "$NEW_FAILURES" -eq 0 ]; then
    SUGGESTION="KEEP"
elif [ "$PASS_COUNT" -eq "$PREV_BEST" ] && [ "$NEW_FAILURES" -eq 0 ]; then
    SUGGESTION="NEUTRAL (no improvement, no regressions)"
else
    SUGGESTION="DISCARD"
fi

# --- Print summary ---
echo ""
echo "================================================================"
echo "  RESULTS: ${PASS_COUNT} passed / ${FAIL_COUNT} failed / ${ERROR_COUNT} errors"
echo "  DELTA:   ${DELTA:+$DELTA} from previous best (${PREV_BEST})"
echo "  TIME:    ${DURATION}s (translate: ${TRANSLATE_TIME}s, test: ${TEST_TIME}s)"
echo "  STATUS:  ${SUGGESTION}"
echo "================================================================"

if [ -n "$NEW_PASSES_LIST" ] && [ "$NEW_PASSES" -gt 0 ]; then
    echo ""
    echo "  NEW PASSES ($NEW_PASSES):"
    echo "$NEW_PASSES_LIST" | sed 's/^/    + /'
fi

if [ -n "$NEW_FAILURES_LIST" ] && [ "$NEW_FAILURES" -gt 0 ]; then
    echo ""
    echo "  REGRESSIONS ($NEW_FAILURES):"
    echo "$NEW_FAILURES_LIST" | sed 's/^/    - /'
fi

echo ""
echo "  Log: $RUN_LOG"
echo "================================================================"

# --- Append to results.tsv ---
# Status is a suggestion; the caller overwrites it after deciding
printf "%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n" \
    "$TIMESTAMP" "$COMMIT" "$PASS_COUNT" "$FAIL_COUNT" "$ERROR_COUNT" \
    "$NEW_PASSES" "$NEW_FAILURES" "$DURATION" \
    "pending" "$DESCRIPTION" >> "$RESULTS_FILE"
