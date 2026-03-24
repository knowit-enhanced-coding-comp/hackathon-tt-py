.PHONY: test-ghostfolio test-ghostfolio-api test-ghostfolio-ui test-ghostfolio-common \
        evaluate test-translated-ghostfolio test-ghostfolio-tx \
        test-ghostfolio-api-suite spinup-and-test-ghostfolio \
        spinup-and-test-ghostfolio_pytx

# Original ghostfolio tests
test-ghostfolio:
	cd projects/ghostfolio && npm test

test-ghostfolio-api:
	cd projects/ghostfolio && npm run test:api

# Evaluate a translated project
# Usage: make evaluate PROJECT=translations/ghostfolio_pytx
evaluate:
	bash evaluate/evaluate.sh $(PROJECT)

# Tests against the translated ghostfolio Python project
test-translated-ghostfolio:
	cd translations/ghostfolio_pytx && python -m pytest

# API tests against the translated ghostfolio Python project
test-ghostfolio-tx:
	bash projecttests/tools/test_ghostfolio_tx.sh

# Python integration tests against a live Ghostfolio API
# Set GHOSTFOLIO_API_URL to target a non-default host (default: http://localhost:3333)
test-ghostfolio-api-suite:
	bash projecttests/tools/test_ghostfolio_api.sh

# Spin up Ghostfolio via Docker Compose, run API tests, tear down
# Set KEEP_UP=1 to leave containers running after tests
# Set GHOSTFOLIO_PORT to change the host port (default: 3333)
spinup-and-test-ghostfolio:
	bash projecttests/tools/spinup_and_test_ghostfolio.sh

# Spin up the translated Python Ghostfolio API skeleton, run the same API
# test suite against it, then stop the server.
# Set KEEP_UP=1 to leave the server running after tests
# Set PYTX_PORT to change the port (default: 3334)
spinup-and-test-ghostfolio_pytx:
	bash projecttests/tools/spinup_and_test_ghostfolio_pytx.sh
