# fwk-playwrightBack-next (Python)

E2E testing framework using **Python + Playwright + pytest** for [demoqa.com](https://demoqa.com).

Refactored from the original TypeScript/Cucumber project. Two branches demonstrate different architectural approaches:

| Branch | Approach | Equivalent to |
|---|---|---|
| `feature/bdd-pom` | pytest-bdd + Gherkin + Page Object Model | TypeScript + Cucumber.js + POM |
| `feature/native-playwright` | Pure pytest + pytest-playwright | TypeScript native `@playwright/test` |

## Stack

- **Python 3.11+**
- **Playwright** (Python) — browser automation
- **pytest** — test runner
- **pytest-bdd** — BDD/Gherkin layer (branch `feature/bdd-pom` only)
- **pytest-playwright** — Playwright fixtures for pytest
- **Faker** — test data generation (replaces `@faker-js/faker`)
- **ruff** — linter + formatter (replaces ESLint + Prettier)
- **mypy** — static type checking (replaces `tsc --noEmit`)
- **taskipy** — task runner (replaces npm scripts)
- **pre-commit** — local git hooks

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
playwright install chromium

python tests/support/generate_data.py   # generate test credentials
task test                                # run all tests
task lint                                # ruff check
task typecheck                           # mypy
```

## Key TypeScript → Python differences

See `docs/interview_cheatsheet.md` for a full comparison.
