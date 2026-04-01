# Enhanced Hackathon 2026

## Setup

### Create your team repository

1. Fork the https://github.com/knowit-enhanced-coding-comp/hackathon-tt-py-example GitHub repository and call it `hackathon-tt-py-[your team name]`.
2. Give `knowit-enhanced-coding-comp` read access to the repository.

## Competition Task: Translation Tool (TT)

Build a **Translation Tool** that translates two TypeScript/JavaScript codebases into Python.

### Rules

1. The TT must **not** use LLMs for the actual translations.
2. You **may** use LLMs to help build the TT itself.
3. You may use the unit tests to verify correctness of the translated code.
4. The team should add a half page to explain their architectural choices.
5. The TT core (`tt/`) must contain **no project-specific mappings** (e.g. no hard-coded `@ghostfolio/…` import paths). Project-specific configuration belongs in `tt_import_map.json` inside the relevant scaffold directory, passed to the translator at call time.
6. TT must not have project-specific logic which it simply copies into the translation. The translated code must be actually translated code, not pregenerated logic.
7. You may use AST libraries.

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
3. We use tools like pyscn for scoring the quality.

### Answer structure

The translation tool should reside in the root folder `tt`.

## Translation Tool (tt)


### Running the translator

```bash
# tt should be able to Translate the default target ghostfolio into translations/ghostfolio_pytx
uv run --project tt tt translate
```

Output should be written to `translations/ghostfolio_pytx/`, mirroring the source directory structure.

### API based test suite

There is an API based test suite which runs against the tt-translated version of ghostfolio. It is invoked with:

```bash
make spinup-and-test-ghostfolio_pytx
```

### Example empty python implementation

| Directory | Purpose |
|---|---|
| `translations/ghostfolio_pytx_example/` | Handwritten reference skeleton — shows how a complete translation should respond to the test suite |

Can be tested with:

```bash
make spinup-and-test-ghostfolio_pytx_example
```

### Translate, then run tests

```bash
make translate-and-test-ghostfolio_pytx
```

This runs `tt translate` to regenerate `translations/ghostfolio_pytx/`, then spins up the FastAPI server and runs the full API test suite against it. Use this as the main iteration loop when improving the translator.

## Testing the Python Translation

### Project layout

| Directory | Purpose |
|---|---|
| `translations/ghostfolio_pytx/` | Output of `tt translate` — the live translation target |
| `translations/ghostfolio_pytx_example/` | Handwritten reference skeleton — shows how a complete translation should respond to the test suite |

### Makefile reference

The Makefile is split into four focused include files under `make/`.  Each group is described below.

---

#### `make/evalsolution.mk` — develop and evaluate the translation tool

The main iteration loop for building `tt`.

| Target | What it does |
|---|---|
| `make evaluate_tt` | Full end-to-end check: translate → verify no LLM/project-specific rules → API tests → scoring |
| `make translate-and-test-ghostfolio_pytx` | Re-translate sources, spin up the FastAPI server on port 3335, run API tests |
| `make spinup-and-test-ghostfolio_pytx` | Spin up the already-translated project on port 3335 and run API tests |
| `make scoring` | Run `pyscn` code-quality scoring on translated code (80%) and `tt/` (20%); write JSON to `evaluate/scoring/results/` |
| `make evaluate PROJECT=…` | Run the generic evaluation script against an arbitrary translated project path |
| `make test-ghostfolio-tx` | Run pytest directly against translated `.py` files (unit tests embedded in the output) |

**Env vars:** `KEEP_UP=1` leaves the server running; `PYTX_PORT` changes the port (default 3335).

---

#### `make/evaloriginal.mk` — test the original Ghostfolio project

Verify the original TypeScript project and establish a ground-truth baseline.

| Target | What it does |
|---|---|
| `make spinup-and-test-ghostfolio` | Start Ghostfolio + Postgres + Redis in Docker, run the full Python API test suite, tear down |
| `make test-ghostfolio` | Run the full Ghostfolio TypeScript test suite (`npm test`) |
| `make test-ghostfolio-api` | Run TypeScript API tests only (`npm run test:api`) |
| `make test-ghostfolio-api-suite` | Run the Python integration tests against an already-running Ghostfolio instance |

**Env vars:** `KEEP_UP=1` leaves containers running; `GHOSTFOLIO_API_URL` targets a non-default host (default `http://localhost:3333`).

Prerequisites: `cd projects/ghostfolio && npm install`. Docker must be running for `spinup-and-test-ghostfolio`.

---

#### `make/evalexamplesolution.mk` — run the handwritten reference skeleton

| Target | What it does |
|---|---|
| `make spinup-and-test-ghostfolio_pytx_example` | Start the `ghostfolio_pytx_example` FastAPI skeleton on port 3334 and run the API test suite |

The reference skeleton (`translations/ghostfolio_pytx_example/`) returns structurally correct but stub responses.  Use it to understand which tests are reachable with a correct API shape, independent of calculation correctness.

**Env vars:** `KEEP_UP=1` leaves the server running; `PYTX_EXAMPLE_PORT` changes the port (default 3334).

---

#### `make/studyoriginal.mk` — TypeScript coverage for Ghostfolio

Measure how much of the original TypeScript source is exercised by tests.  Useful for understanding which code paths need to be translated and verified.

| Target | What it does |
|---|---|
| `make coverage-ghostfolio-ts` | Run Jest with coverage; report written to `projects/ghostfolio/coverage/apps/api/lcov-report/index.html` |
| `make coverage-ghostfolio-integration` | Build Ghostfolio from source, run Python integration tests with `NODE_V8_COVERAGE`, generate HTML + lcov report mapped back to TypeScript source; output at `coverage/ghostfolio-integration/html/index.html` |

Prerequisites: `cd projects/ghostfolio && npm install`. Docker must be running for `coverage-ghostfolio-integration`.

---

All spinup targets share this lifecycle:

1. Sync Python deps via `uv`
2. Start `uvicorn` on the configured port
3. Wait up to 30 s for `GET /api/v1/health`
4. Run `projecttests/ghostfolio_api/` with pytest
5. Stop the server on exit

### ghostfolio_pytx_example — the reference skeleton

`translations/ghostfolio_pytx_example/` is a **handwritten** FastAPI implementation that demonstrates how a correctly translated project should respond to the API test suite. It is not generated by `tt` — it is a manually crafted baseline. Run tests against it to see the floor (≈23/60 tests pass with stub calculations).

See `translations/ghostfolio_pytx_example/README.md` for details.

### Why some tests pass and others fail

The stub `app/main.py` in both projects returns zero/empty values for all portfolio calculations. Despite this, some tests pass:

**Tests that pass (≈23/60):**

- **Empty-is-correct assertions** — tests asserting `investments` is `[]`, `holdings` is `{}`, `chart` is `[]`, or `totalFees` is zero match the stub exactly.
- **Simple buy-minus-sell formula** — `totalInvestment` is computed as `sum(BUY qty × unitPrice) − sum(SELL qty × unitPrice)`. Correct for buy-only portfolios and fully-closed positions.
- **Accessibility-only assertions** — some tests only check that a field exists or that the HTTP response is 200.

**Tests that fail (≈37/60):**

- **Chart history** — `chart` is always `[]`.
- **Current value / net performance** — `currentValue`, `netPerformance`, and related fields are always `0.0`.
- **Holdings** — `holdings` is always `{}`.
- **Grouped investments** — `investments` is always `[]`; no monthly/yearly grouping.
- **Cost-basis tracking** — partial sell scenarios need average-cost tracking, not simple price arithmetic.

To make more tests pass, implement the portfolio calculation logic in `translations/ghostfolio_pytx/app/main.py`, drawing from the translated calculator at `translations/ghostfolio_pytx/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.py`.

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

## Judging

Judges might evaluate submissions using Claude Code skills that inspect the `tt` source code and test results directly inside a Claude Code session.

### explain-tt-strategy

Reads all Python source files under `tt/tt/` and produces a concise technical explanation of the translation strategy — pipeline structure, what each regex pass does, key design decisions, and trade-offs.

**How to use:**

Open Claude Code in this repository and run:

```
/explain-tt-strategy
```

Claude will read `tt/tt/translator.py`, `cli.py`, `runner.py`, and any other modules present, then output a structured analysis covering:

- How the translation pipeline is structured (passes, ordering, why order matters)
- What each major pass handles (TS constructs → Python equivalents)
- Key design decisions (no AST, regex-only, approximate output)
- Notable patterns, helper mappings, or edge cases

The skill is defined in `.claude/commands/explain-tt-strategy.md`.

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
