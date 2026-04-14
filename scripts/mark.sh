#!/usr/bin/env bash
# mark.sh — Update the status of the last experiment in results.tsv
#
# Usage:
#   bash scripts/mark.sh keep       # mark last experiment as kept
#   bash scripts/mark.sh discard    # mark last experiment as discarded
#   bash scripts/mark.sh baseline   # mark last experiment as baseline
#   bash scripts/mark.sh crash      # mark last experiment as crashed
#
# This edits the last row of results.tsv in-place.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_FILE="$ROOT_DIR/results.tsv"
STATUS="${1:?Usage: bash scripts/mark.sh <keep|discard|baseline|crash>}"

if [ ! -f "$RESULTS_FILE" ] || [ "$(wc -l < "$RESULTS_FILE")" -le 1 ]; then
    echo "No results to mark."
    exit 1
fi

case "$STATUS" in
    keep|discard|baseline|crash|pending) ;;
    *) echo "Invalid status: $STATUS (must be keep|discard|baseline|crash)"; exit 1 ;;
esac

# Replace the status field (column 9) in the last row
# Using a temp file for portability (macOS sed -i differs from GNU)
LAST_LINE=$(tail -1 "$RESULTS_FILE")
NEW_LINE=$(echo "$LAST_LINE" | awk -F'\t' -v s="$STATUS" 'BEGIN{OFS="\t"} {$9=s; print}')

# Replace last line
head -n -1 "$RESULTS_FILE" > "$RESULTS_FILE.tmp"
echo "$NEW_LINE" >> "$RESULTS_FILE.tmp"
mv "$RESULTS_FILE.tmp" "$RESULTS_FILE"

echo "Marked last experiment as: $STATUS"
