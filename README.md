# fwk-playwrightBack-next (Python)

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
- **Playwright** (Python) — browser automation
- **pytest** — test runner
- **pytest-bdd** — BDD/Gherkin layer (`feature/bdd-pom` branch only)
- **pytest-playwright** — Playwright fixtures for pytest (`feature/native-playwright-reports` branch)
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
