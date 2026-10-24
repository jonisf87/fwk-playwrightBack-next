# fwk-playwrightBack-next (Python)

[![CI](https://github.com/jonisf87/fwk-playwrightBack-next/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jonisf87/fwk-playwrightBack-next/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Playwright](https://img.shields.io/badge/playwright-1.64-green)

E2E testing framework using **Python + Playwright + pytest** for [demoqa.com](https://demoqa.com).

Refactored from the original TypeScript/Cucumber project. Three branches demonstrate different architectural approaches:

| Branch | Approach | Equivalent to |
|---|---|---|
| `feature/bdd-pom` | pytest-bdd + Gherkin + Page Object Model | TypeScript + Cucumber.js + POM |
| `feature/native-playwright` | Pure pytest, **async API**, manual lifecycle | TypeScript `@playwright/test` (async) |
| `feature/native-playwright-reports` | Pure pytest, **sync API**, lifecycle delegated to pytest-playwright | TypeScript `@playwright/test` with native screenshot/trace |

## Why one branch is async and the other is not

### `feature/native-playwright` → async

This branch manages the Playwright lifecycle manually (`async_playwright`, `Browser`, `BrowserContext`, `Page` as async fixtures). Using the async API unlocks `asyncio.gather()`, which enables **true concurrent** execution of multiple browser contexts within the same test — the Python equivalent of `Promise.all()`:

```python
await asyncio.gather(
    run_user_flow(ctx_a, page_a),
    run_user_flow(ctx_b, page_b),
)
```

The cost: high boilerplate in `conftest.py` (6 async fixtures) and `asyncio_mode = "auto"` required in `pyproject.toml`.

### `feature/native-playwright-reports` → sync

This branch delegates the entire lifecycle to the `pytest-playwright` plugin, which provides `page`, `browser`, `context`, and `api_request_context` out of the box. Using the sync API reduces `conftest.py` to a **single override** (`base_url`). The trade-off: `asyncio.gather()` is gone — the parallel-users test becomes sequential (user 1 completes, then user 2 starts).

The gain is native artifact capture with zero extra code:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--screenshot=only-on-failure --tracing=retain-on-failure"
```

Equivalent to `playwright.config.ts` with `screenshot: 'only-on-failure'` and `trace: 'retain-on-failure'`.

### Trade-off summary

| | `feature/native-playwright` | `feature/native-playwright-reports` |
|---|---|---|
| Playwright API | async (`await`) | sync |
| Lifecycle fixtures | Manual (6 fixtures) | Delegated to pytest-playwright |
| True concurrency | ✅ `asyncio.gather()` | ❌ Sequential |
| Automatic screenshots/traces | ❌ Manual | ✅ Native |
| conftest boilerplate | High | Minimal |

---

## Stack

- **Python 3.11+**
- **Playwright** (Python) 1.64 — browser automation
- **pytest** 9.1 — test runner
- **pytest-asyncio** 1.4 — async tests (`feature/native-playwright` branch)
- **pytest-bdd** 9.0 — BDD/Gherkin layer (`feature/bdd-pom` branch only; that branch pins `<8.0`, see its README)
- **pytest-playwright** 0.10 — Playwright fixtures for pytest (`feature/native-playwright-reports` branch)
- **Faker** 40 — test data generation (replaces `@faker-js/faker`)
- **ruff** 0.17 — linter + formatter (replaces ESLint + Prettier)
- **mypy** 2.4 — static type checking (replaces `tsc --noEmit`)
- **taskipy** 1.14 — task runner (replaces npm scripts)
- **pre-commit** 4.7 — local git hooks

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
playwright install --with-deps chromium

python tests/support/generate_data.py   # generate test credentials
task test                                # run all tests (needs a branch that contains tests, see above)
task lint                                # ruff check
task typecheck                           # mypy
```

## CI

`main` only carries the shared base (page objects, support code, tooling), so its workflow (`.github/workflows/ci.yml`) runs lint, format check and mypy. Each feature branch has its own workflow that also runs the E2E tests.
