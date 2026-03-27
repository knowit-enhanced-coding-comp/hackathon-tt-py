.PHONY: coverage-ghostfolio-ts coverage-ghostfolio-integration

# Run the Ghostfolio API TypeScript unit tests with Jest coverage.
# Coverage report written to projects/ghostfolio/coverage/apps/api/
# (lcov, text-summary, and HTML formats).
# Requires: cd projects/ghostfolio && npm install
coverage-ghostfolio-ts:
	cd projects/ghostfolio && npx dotenv-cli -e .env.example -- npx nx test api --coverage
	@echo "Coverage report: projects/ghostfolio/coverage/apps/api/lcov-report/index.html"

# Build Ghostfolio from source, run integration tests with NODE_V8_COVERAGE,
# and generate an HTML + lcov coverage report mapped back to TypeScript source.
# Output: coverage/ghostfolio-integration/html/index.html
coverage-ghostfolio-integration:
	bash projecttests/tools/coverage_ghostfolio_integration.sh
