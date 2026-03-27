#!/usr/bin/env bash
# run_quality_checks.sh — Code quality evaluation suite for the tt translator.
#
# Usage:
#   bash evaluate/checks/run_quality_checks.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "--- Code quality checks ---"

uv run --project "$ROOT_DIR/tt" python "$SCRIPT_DIR/detect_llm_usage.py"
uv run --project "$ROOT_DIR/tt" python "$SCRIPT_DIR/detect_direct_mappings.py"

echo "Code quality checks: OK"
