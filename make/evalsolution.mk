# ---------------------------------------------------------------------------
# evalsolution.mk — evaluate, test, and score the tt-translated project
#
# This file contains the main iteration loop for developing the translation
# tool (tt).  Use evaluate_tt for the full end-to-end check; use the
# individual spinup/translate targets for faster feedback during development.
#
# Port used by the translated project: 3335 (set PYTX_PORT to override)
# ---------------------------------------------------------------------------
.PHONY: evaluate test-translated-ghostfolio test-ghostfolio-tx test-ghostfolio-pytx \
        spinup-and-test-ghostfolio_pytx \
        translate-and-test-ghostfolio_pytx evaluate_tt \
        scoring_codequality scoring detect_rule_breaches

# Evaluate a translated project
# Usage: make evaluate PROJECT=translations/ghostfolio_pytx
evaluate:
	bash evaluate/evaluate.sh $(PROJECT)

# Tests against the translated ghostfolio Python project
test-translated-ghostfolio:
	cd translations/ghostfolio_pytx && python -m pytest

# Run pytest directly against the tt-translated output in translations/ghostfolio_pytx
# (unit tests embedded in the translated files)
test-ghostfolio-tx:
	bash projecttests/tools/test_ghostfolio_tx.sh

# Alias for test-ghostfolio-tx
test-ghostfolio-pytx:
	bash projecttests/tools/test_ghostfolio_tx.sh

# Spin up the tt-translated Python project in translations/ghostfolio_pytx,
# run the API test suite against it, then stop the server.
# Set KEEP_UP=1 to leave the server running after tests
# Set PYTX_PORT to change the port (default: 3335)
spinup-and-test-ghostfolio_pytx:
	bash projecttests/tools/kill_ghostfolio_pytx.sh
	bash projecttests/tools/spinup_and_test_ghostfolio_pytx.sh
	bash projecttests/tools/kill_ghostfolio_pytx.sh

# Run tt translate to (re)generate translations/ghostfolio_pytx, then spin up
# the server and run the full API test suite against it.
translate-and-test-ghostfolio_pytx:
	bash projecttests/tools/kill_ghostfolio_pytx.sh
	uv run --project tt tt translate
	bash projecttests/tools/spinup_and_test_ghostfolio_pytx.sh

# Full evaluation of the tt translator:
#   1. Translate sources (timed) and verify no LLM is used
#   2. Run API integration tests against the translated project
#   3. Run the code quality check suite
evaluate_tt:
	@echo "=== [1/3] Translate (timed) ==="
	rm -rf translations/ghostfolio_pytx
	time uv run --project tt tt translate
	@echo "=== [2/3] API tests + scoring against translated version ==="
	-bash projecttests/tools/spinup_and_test_ghostfolio_pytx.sh
	-bash projecttests/tools/kill_ghostfolio_pytx.sh
	-bash projecttests/tools/start_ghostfolio_pytx.sh
	-$(MAKE) scoring
	-bash projecttests/tools/kill_ghostfolio_pytx.sh
	@echo "=== [3/3] Code quality checks ==="
	-bash evaluate/checks/run_quality_checks.sh

# Run pyscn code quality scoring on translated code and tt itself.
# Produces a weighted score (translated=80%, tt=20%) and writes JSON to
# evaluate/scoring/results/latest.json
scoring_codequality:
	uv run --project tt python evaluate/scoring/codequality.py

# Run both successful-tests scoring and pyscn code quality scoring, then print a combined overall score.
scoring:
	@echo "=== [1/3] Successful tests score ==="
	-uv run --project tt python evaluate/scoring/successfultests.py
	@echo "=== [2/3] Code quality score ==="
	-uv run --project tt python evaluate/scoring/codequality.py
	@echo "=== [3/3] Overall score (50% tests + 50% code quality) ==="
	-uv run --project tt python evaluate/scoring/overall.py

# Run all implementation-rule detection scripts against tt/ source.
detect_rule_breaches:
	bash evaluate/checks/detect_rule_breaches.sh
