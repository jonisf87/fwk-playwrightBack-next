# Playwright Python Framework (native-playwright-reports branch)

End-to-end testing framework for [demoqa.com](https://demoqa.com) built with Python, pytest-playwright, and pytest. This branch demonstrates the **pytest-playwright approach**: tests written as plain `def test_*` functions (sync, no `await`) with pytest-playwright providing the full browser lifecycle and native artifact capture.

If you come from TypeScript, think of this branch as the Python equivalent of `@playwright/test` with `screenshot: 'only-on-failure'` and `trace: 'retain-on-failure'` enabled. You get screenshots and traces for free on failure — no extra code.

---

## What makes this branch different

There are three branches in this repository, each showing a different testing architecture:

| Aspect | feature/bdd-pom | feature/native-playwright | This branch |
|---|---|---|---|
| Test format | Gherkin `.feature` files | `async def test_*` | `def test_*` (sync) |
| Playwright API | sync (pytest-bdd constraint) | async (full `await`) | sync (pytest-playwright) |
| Browser lifecycle | Manual (conftest fixtures) | Manual (conftest fixtures) | Delegated to pytest-playwright |
| Concurrency | Sequential | Real (`asyncio.gather`) | Sequential (two contexts) |
| Screenshots on failure | Manual | Manual | Automatic (`--screenshot`) |
| Traces on failure | Manual | Manual | Automatic (`--tracing`) |
| Boilerplate in conftest | High (7 fixtures) | High (6 async fixtures) | Zero (1 override) |

The headline feature of this branch is **zero lifecycle boilerplate**. The entire `conftest.py` is a single fixture override:

```python
@pytest.fixture(scope="session")
def base_url() -> str:
    return "https://demoqa.com"
```

pytest-playwright provides `page`, `browser`, `context`, and `api_request_context` out of the box. You just use them in tests.

**Trade-off vs feature/native-playwright**: by switching to pytest-playwright's sync API, we lose `asyncio.gather()`. The parallel-users test becomes sequential (user 1 completes, then user 2 starts). The TypeScript equivalent of `Promise.all()` is only available in the `feature/native-playwright` branch.

---

## How native artifacts work

pytest-playwright hooks into pytest's reporting lifecycle. When a test fails:

1. A PNG screenshot is saved to `test-results/<test-name>/test-failed-1.png`
2. A trace archive is saved to `test-results/<test-name>/trace.zip`

These are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--screenshot=only-on-failure --tracing=retain-on-failure"
```

Equivalent to `playwright.config.ts`:

```typescript
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
})
```

To open a trace after a failure:

```bash
playwright show-trace test-results/<test-name>/trace.zip
```

The trace viewer is interactive: it shows DOM snapshots, network requests, console logs, and a timeline for every action.

---

## Project structure

```
tests/
├── conftest.py               # Single base_url override (pytest-playwright handles the rest)
├── pages/
│   ├── login_page.py         # Page Object for demoqa.com/login (sync)
│   ├── registration_page.py  # Page Object for demoqa.com/register (sync)
│   ├── practice_form_page.py # Page Object for the practice form (sync)
│   └── sortable_page.py      # Page Object for demoqa.com/sortable (sync)
├── fixtures/
│   └── test-image.png        # image file used in the file upload test
├── support/
│   ├── generate_data.py      # generates test credentials and writes them to data.json
│   └── data.json             # persisted credentials (git-ignored)
├── test_api.py               # 3 API tests (register, token, authenticated user)
├── test_login.py             # 2 login tests (valid and invalid credentials)
├── test_registration.py      # 2 registration tests (valid and invalid password)
└── test_parallel_users.py    # 2 tests with two browser contexts (sequential)
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

playwright install chromium

python tests/support/generate_data.py
```

---

## Running the tests

```bash
task test

task test-api

task test-ui

pytest tests/ -v --browser firefox

pytest tests/test_parallel_users.py -v
```

After a failure, artifacts land in `test-results/<test-name>/`:

```bash
playwright show-trace test-results/<test-name>/trace.zip
```

---

## Code quality

```bash
task lint
task format
task format-check
task typecheck
```

---

## Key concepts worth knowing

**pytest-playwright owns the fixture tree**
When you write `def test_something(page: Page)`, pytest-playwright creates a browser, a context, and a page for you. The `page` fixture is function-scoped by default (a fresh page per test). You never call `async_playwright()` or `browser.new_context()` yourself.

**`base_url` integration**
Because `base_url` is set to `"https://demoqa.com"`, calling `page.goto("/login")` resolves to `https://demoqa.com/login`. This is identical to `playwright.config.ts { use: { baseURL: 'https://demoqa.com' } }`.

**`api_request_context` vs `page.request`**
pytest-playwright provides an `api_request_context` fixture that creates a standalone HTTP client (no browser, no page). It respects `base_url` so API tests can use `/Account/v1/User` as the path. In TypeScript this is `request.newContext()`.

**`response.status` is a property, not a method**
The most common mistake when porting from TypeScript: `response.status()` (method call) becomes `response.status` (integer property, no parentheses) in Python. Writing `response.status()` returns a bound method object, which is always truthy — assertions never fail even on 404 or 500 responses.

**`--browser` flag on the CLI**
pytest-playwright uses `--browser chromium` (or `firefox`, `webkit`) as a CLI flag. This is how CI passes the browser matrix value — different from the `feature/native-playwright` branch which used a `BROWSER` environment variable.

**Sync vs async API**
This branch imports from `playwright.sync_api`. The `feature/native-playwright` branch imports from `playwright.async_api`. Both expose the same methods but the sync version blocks the thread; the async version returns coroutines that must be awaited. pytest-playwright works exclusively with `sync_api`.

---

## CI/CD

The workflow `.github/workflows/native-playwright-reports.yml` runs three jobs:

```
lint  →  ui-tests (chromium + firefox, in parallel)
      →  api-tests
```

On failure, the `test-results/` directory (screenshots and traces) is uploaded as a CI artifact that can be downloaded from the Actions run page.
