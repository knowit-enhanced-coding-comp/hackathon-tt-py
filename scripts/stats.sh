#!/usr/bin/env bash
# stats.sh — Show improvement stats from results.tsv
#
# Usage:
#   bash scripts/stats.sh           # full summary
#   bash scripts/stats.sh --last N  # last N experiments
#   bash scripts/stats.sh --keeps   # only kept experiments
#   bash scripts/stats.sh --csv     # machine-readable output
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_FILE="$ROOT_DIR/results.tsv"

if [ ! -f "$RESULTS_FILE" ] || [ "$(wc -l < "$RESULTS_FILE")" -le 1 ]; then
    echo "No results yet. Run: bash scripts/evaluate.sh 'baseline'"
    exit 0
fi

MODE="${1:---summary}"
LAST_N="${2:-999999}"

case "$MODE" in
    --last)
        echo "=== Last $LAST_N experiments ==="
        echo ""
        printf "%-20s %-9s %5s %5s %5s %6s %8s %-10s %s\n" \
            "TIMESTAMP" "COMMIT" "PASS" "FAIL" "NEW+" "NEW-" "TIME(s)" "STATUS" "DESCRIPTION"
        printf "%-20s %-9s %5s %5s %5s %6s %8s %-10s %s\n" \
            "-------------------" "-------" "----" "----" "----" "-----" "-------" "---------" "-----------"
        tail -n +2 "$RESULTS_FILE" | tail -n "$LAST_N" | while IFS=$'\t' read -r ts commit pass fail err new_p new_f dur status desc; do
            printf "%-20s %-9s %5d %5d %5d %6d %8d %-10s %s\n" \
                "$ts" "$commit" "$pass" "$fail" "$new_p" "$new_f" "$dur" "$status" "$desc"
        done
        ;;

    --keeps)
        echo "=== Kept experiments (improvements only) ==="
        echo ""
        printf "%-20s %-9s %5s %5s %8s %s\n" \
            "TIMESTAMP" "COMMIT" "PASS" "FAIL" "TIME(s)" "DESCRIPTION"
        printf "%-20s %-9s %5s %5s %8s %s\n" \
            "-------------------" "-------" "----" "----" "-------" "-----------"
        tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "keep" || $9 == "baseline"' | while IFS=$'\t' read -r ts commit pass fail err new_p new_f dur status desc; do
            printf "%-20s %-9s %5d %5d %8d %s\n" \
                "$ts" "$commit" "$pass" "$fail" "$dur" "$desc"
        done
        ;;

    --csv)
        cat "$RESULTS_FILE"
        ;;

    --summary|*)
        TOTAL_EXPERIMENTS=$(( $(wc -l < "$RESULTS_FILE") - 1 ))
        KEEPS=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "keep" || $9 == "baseline"' | wc -l | tr -d ' ')
        DISCARDS=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "discard"' | wc -l | tr -d ' ')
        CRASHES=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "crash"' | wc -l | tr -d ' ')
        PENDING=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "pending"' | wc -l | tr -d ' ')

        FIRST_PASS=$(tail -n +2 "$RESULTS_FILE" | head -1 | awk -F'\t' '{print $3}')
        LATEST_PASS=$(tail -1 "$RESULTS_FILE" | awk -F'\t' '{print $3}')
        BEST_PASS=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' 'BEGIN{max=0} {if($3+0>max) max=$3+0} END{print max}')
        FIRST_FAIL=$(tail -n +2 "$RESULTS_FILE" | head -1 | awk -F'\t' '{print $4}')
        LATEST_FAIL=$(tail -1 "$RESULTS_FILE" | awk -F'\t' '{print $4}')

        TOTAL_GAIN=$((BEST_PASS - FIRST_PASS))
        AVG_DURATION=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '{sum+=$8; n++} END {if(n>0) printf "%.0f", sum/n; else print 0}')

        FIRST_TS=$(tail -n +2 "$RESULTS_FILE" | head -1 | awk -F'\t' '{print $1}')
        LATEST_TS=$(tail -1 "$RESULTS_FILE" | awk -F'\t' '{print $1}')

        echo "================================================================"
        echo "  AUTORESEARCH LOOP STATS"
        echo "================================================================"
        echo ""
        echo "  Experiments:    $TOTAL_EXPERIMENTS total"
        echo "    Kept:         $KEEPS"
        echo "    Discarded:    $DISCARDS"
        echo "    Crashed:      $CRASHES"
        echo "    Pending:      $PENDING"
        echo "  Hit rate:       $(awk "BEGIN {if($TOTAL_EXPERIMENTS>0) printf \"%.0f\", $KEEPS/$TOTAL_EXPERIMENTS*100; else print 0}")%"
        echo ""
        echo "  First run:      $FIRST_PASS passed / $FIRST_FAIL failed ($FIRST_TS)"
        echo "  Latest run:     $LATEST_PASS passed / $LATEST_FAIL failed ($LATEST_TS)"
        echo "  Best ever:      $BEST_PASS passed"
        echo "  Total gain:     +$TOTAL_GAIN tests from baseline"
        echo ""
        echo "  Avg cycle time: ${AVG_DURATION}s"
        echo ""
        echo "  Score estimate: $(awk "BEGIN {printf \"%.1f\", ($BEST_PASS / 135.0) * 85}")% (test component, 85% weight)"
        echo "================================================================"

        # Show improvement timeline (kept experiments only)
        KEEP_COUNT=$(tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "keep" || $9 == "baseline"' | wc -l | tr -d ' ')
        if [ "$KEEP_COUNT" -gt 0 ]; then
            echo ""
            echo "  IMPROVEMENT TIMELINE:"
            tail -n +2 "$RESULTS_FILE" | awk -F'\t' '$9 == "keep" || $9 == "baseline"' | while IFS=$'\t' read -r ts commit pass fail err new_p new_f dur status desc; do
                BAR=""
                for i in $(seq 1 $((pass / 3))); do BAR="${BAR}#"; done
                printf "    %s  %3d/135  %s  %s\n" "$commit" "$pass" "$BAR" "$desc"
            done
        fi
        echo ""
        ;;
esac
