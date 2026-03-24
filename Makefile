.PHONY: test-ghostfolio test-ghostfolio-api test-ghostfolio-ui test-ghostfolio-common \
        evaluate test-translated-ghostfolio test-ghostfolio-tx test-ghostfolio-pytx \
        test-ghostfolio-api-suite spinup-and-test-ghostfolio \
        spinup-and-test-ghostfolio_pytx_example spinup-and-test-ghostfolio_pytx

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

# Run pytest directly against the tt-translated output in translations/ghostfolio_pytx
# (unit tests embedded in the translated files)
test-ghostfolio-tx:
	bash projecttests/tools/test_ghostfolio_tx.sh

# Alias for test-ghostfolio-tx
test-ghostfolio-pytx:
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

# Spin up the ghostfolio_pytx_example reference skeleton, run the API test suite,
# then stop the server. The example shows how a translated API should respond.
# Set KEEP_UP=1 to leave the server running after tests
# Set PYTX_EXAMPLE_PORT to change the port (default: 3334)
spinup-and-test-ghostfolio_pytx_example:
	bash projecttests/tools/spinup_and_test_ghostfolio_pytx_example.sh

# Spin up the tt-translated Python project in translations/ghostfolio_pytx,
# run the API test suite against it, then stop the server.
# Set KEEP_UP=1 to leave the server running after tests
# Set PYTX_PORT to change the port (default: 3335)
spinup-and-test-ghostfolio_pytx:
	bash projecttests/tools/spinup_and_test_ghostfolio_pytx.sh
