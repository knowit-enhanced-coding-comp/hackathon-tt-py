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

### TODO: Explain how to run tests against your translated versions

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
