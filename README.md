# Enhanced Hackathon 2026

## Setup

### Create your team repository

1. Fork the https://github.com/knowit-enhanced-coding-comp/hackathon-tt-py-example GitHub repository and call it `hackathon-tt-py-[your team name]`.
2. Give `knowit-enhanced-coding-comp` read access to the repository.

## Competition Task: Translation Tool (TT)

Build a **Translation Tool** that translates two TypeScript/JavaScript codebases into Python.

### Rules

- The TT must **not** use LLMs for the actual translations.
- You **may** use LLMs to help build the TT itself.
- You may use the unit tests to verify correctness of the translated code.
- The team should add a half page to explain their architectural choices.

### Judging Criteria

The TT will be judged on:

1. **Correctness** — translated Python code passes the API tests of the reference projects, and how many of them
2. **Python code quality**, ranked by relevance:
   1. Simplicity as Discipline
   2. Testing & Verification
   3. Elegance & Readability
   4. Iterative Delivery
   5. Humility & Scope Limits
   6. Long-term Sustainability
   7. Data Structures First
   8. Customer-First Thinking
   9. Avoid Duplication (DRY)
   10. Understand the Metal

### Answer structure

The translation tool reside in the root folder `tt`.

## Testing the Python Translation: ghostfolio_pytx

### What is ghostfolio_pytx?

`translations/ghostfolio_pytx/` is a **Python skeleton** of the Ghostfolio portfolio API built with FastAPI. It is a translation target — a stub that implements all the required API endpoints with structurally correct responses but without real portfolio calculation logic. Its purpose is to let you run the full integration test suite locally and incrementally implement the calculations until all tests pass.

The skeleton keeps all state in memory (no database). Each test creates and deletes its own user, so tests are isolated from each other.

### Running the tests

```bash
make spinup-and-test-ghostfolio_pytx
```

This command:

1. Syncs Python dependencies for `translations/ghostfolio_pytx` using `uv`.
2. Starts a `uvicorn` server on port **3334** in the background.
3. Waits up to 30 seconds for `GET /api/v1/health` to return 200.
4. Runs the same integration test suite (`projecttests/ghostfolio_api/`) used for the original Ghostfolio, pointing it at `http://localhost:3334`.
5. Stops the server when tests finish.

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `PYTX_PORT` | `3334` | Host port for the skeleton server |
| `KEEP_UP` | `0` | Set to `1` to leave the server running after tests |

### Why some tests pass and others fail

The skeleton intentionally returns zero/empty values for all portfolio calculations. Despite this, some tests pass because:

**Tests that pass (≈22/60):**

- **Empty-is-correct assertions** — tests that assert `investments` is an empty list, `holdings` is an empty dict, `chart` is an empty list, or `totalFees` is zero. The stub returns exactly these values, so these assertions match.
- **Simple buy-minus-sell price formula** — the stub computes `totalInvestment` as `sum(BUY qty × unitPrice) − sum(SELL qty × unitPrice)`. For buy-only portfolios and for portfolios where all positions are fully closed (total cost basis nets to zero), this formula gives the correct answer.
- **Accessibility-only assertions** — some tests only check that a field exists or that an HTTP response is 200, without asserting a specific calculated value.

**Tests that fail (≈38/60):**

These tests require real portfolio calculations that are not yet implemented in the skeleton:

- **Chart history** — `chart` is always `[]`; tests asserting specific data points or a non-empty chart fail.
- **Current market value / net performance** — `currentValue`, `netPerformance`, `netPerformancePercentage`, and related fields are always `0.0`; tests expecting non-zero performance figures fail.
- **Holdings** — `holdings` is always `{}`; tests asserting specific holding quantities, allocation percentages, or per-symbol data fail.
- **Grouped investments** — `investments` is always `[]`; tests asserting investment entries grouped by month or year fail.
- **Cost-basis tracking** — buy/sell sequences where the correct `totalInvestment` depends on tracking average cost (not just summing prices) produce wrong results.

To make more tests pass, implement the portfolio calculation logic inside `translations/ghostfolio_pytx/app/main.py`.

## The translated projects

The auto translated versions should be saved in `translations`.

The project ghostfolio should be translated to `ghostfolio_pytx`.

## Evaluating the translated version

Run

```make evaluate [translated project name]```

Where portnumber is the port number where the API of the translated version is running.
e.g.

```
make evaluate translations/ghostfolio_pytx
```

## Running Original Tests

### projects/ghostfolio

Ghostfolio uses [Nx](https://nx.dev/) as its build system and requires Node.js >= 22.18.0.

Install dependencies first:

```bash
cd projects/ghostfolio
npm install
```

Run all tests (requires a `.env.example` file with database config):

```bash
npm test
```

This runs `npx dotenv-cli -e .env.example -- npx nx run-many --target=test --all --parallel=4`.

Run tests for specific packages:

```bash
npm run test:api     # API tests only
npm run test:ui      # UI tests only
npm run test:common  # Common library tests only
```

### projects/cal.com

Cal.com uses [Yarn](https://yarnpkg.com/) (v4+) and [Turbo](https://turbo.build/). Tests are run with [Vitest](https://vitest.dev/).

Install dependencies first:

```bash
cd projects/cal.com
yarn
```

Run unit tests:

```bash
TZ=UTC yarn test
```

The `TZ=UTC` prefix is required for consistent timezone handling across environments.

Run E2E tests (requires a running database and seeded data):

```bash
yarn db-seed && yarn e2e
```

Run E2E tests for specific targets:

```bash
yarn e2e:app-store    # App store E2E tests
yarn e2e:embed        # Embed E2E tests
```
