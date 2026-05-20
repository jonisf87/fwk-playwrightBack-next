# Playwright Python Framework (native-playwright branch)

End-to-end testing framework for [demoqa.com](https://demoqa.com) built with Python, Playwright, and pytest. This branch demonstrates the **native approach**: tests written as plain `async def test_*` functions with no Gherkin/BDD layer on top.

If you come from TypeScript, think of this branch as the Python equivalent of writing tests directly with `@playwright/test`. The other branch (`feature/bdd-pom`) is the Cucumber.js equivalent.

---

## What makes this branch different

The headline feature is `asyncio.gather()`. It lets two simulated users run **truly concurrently** in the same test, which is something the BDD branch cannot do because its step functions are synchronous.

```python
# Both users start AT THE SAME TIME (not one after the other)
form_submitted, grid_changed = await asyncio.gather(
    _user1_form_task(browser),
    _user2_grid_task(browser),
)
```

The TypeScript equivalent is:
```typescript
const [formSubmitted, gridChanged] = await Promise.all([
    user1FormTask(browser),
    user2GridTask(browser),
])
```

---

## Project structure

```
tests/
├── conftest.py               # async fixtures (playwright_instance, browser, page, api_request_context)
├── pages/
│   ├── login_page.py         # Page Object for demoqa.com/login (async)
│   ├── registration_page.py  # Page Object for demoqa.com/register (async)
│   ├── practice_form_page.py # Page Object for the practice form (async)
│   └── sortable_page.py      # Page Object for demoqa.com/sortable (async)
├── fixtures/
│   └── test-image.png        # image file used in the file upload test
├── support/
│   ├── generate_data.py      # generates test credentials and writes them to data.json
│   └── data.json             # persisted credentials (git-ignored)
├── test_api.py               # 3 API tests (register, token, authenticated user)
├── test_login.py             # 2 login tests (valid and invalid credentials)
├── test_registration.py      # 2 registration tests (valid and invalid password)
└── test_parallel_users.py    # 2 tests using asyncio.gather() (the key differentiator)
```

---

## Setup

```bash
# Create a virtual environment and install all dependencies (equivalent to npm install)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Install Playwright browsers (equivalent to npx playwright install)
playwright install chromium

# Generate test credentials (creates tests/support/data.json)
python tests/support/generate_data.py
```

---

## Running the tests

```bash
# All tests
task test

# API tests only (no browser, much faster)
task test-api

# UI tests only (opens a browser)
task test-ui

# With a specific browser (defaults to chromium)
BROWSER=firefox task test-ui

# Verbose output
pytest tests/ -v

# One specific test
pytest tests/test_parallel_users.py::test_two_users_parallel -v
```

---

## Code quality

```bash
task lint          # ruff check (equivalent to ESLint)
task format        # ruff format (equivalent to Prettier)
task format-check  # check formatting without modifying files
task typecheck     # mypy strict (equivalent to tsc --noEmit)
```

---

## Key concepts worth knowing

**`asyncio_mode = "auto"` in pyproject.toml**
pytest-asyncio automatically detects `async def test_*` functions and runs each one inside `asyncio.run()`. Without this setting, async tests are collected but their body never executes (the coroutine object is created but never awaited).

**`async with async_playwright()` in conftest.py**
Unlike the BDD branch which uses `with sync_playwright()`, the context manager here is async because its `__aenter__` and `__aexit__` are coroutines. Every fixture is `async def` and every Playwright call is `await`-ed.

**`response.status` is a property, not a method**
The most common mistake when porting from TypeScript: in TS you write `response.status()` (method call), in Python it is `response.status` (integer property, no parentheses). Writing `response.status()` in Python returns a bound method object, which is always truthy, so assertions never fail even on 404 or 500 responses.

**`await response.json()` vs `response.json()`**
In the BDD branch (sync_api), calling `response.json()` returns the parsed body directly. In this branch (async_api), the same method is a coroutine and must be awaited: `body = await response.json()`.

**`page.evaluate("() => { ... }")` receives a JS string**
In TypeScript you can pass a real lambda function. In Python the argument must be a string containing JavaScript source code, because Python functions cannot be serialized to JS.

**`asyncio.gather()` vs `Promise.all()`**
Both schedule all coroutines (or promises) to start at the same time on a single event loop. While one task waits for a network response, the event loop advances the other. This is cooperative concurrency (single thread, multiple coroutines), not multi-threading.

---

## CI/CD

The workflow `.github/workflows/native-playwright.yml` runs three jobs:

```
lint  →  ui-tests (chromium + firefox, in parallel)
      →  api-tests
```

UI tests only run if lint passes first. API tests and UI tests run in parallel with each other.

---

## Comparison with feature/bdd-pom

| Aspect | This branch (native) | BDD branch |
|---|---|---|
| Playwright API | `async_api` (await everywhere) | `sync_api` (no await) |
| Test format | `async def test_*` functions | `@given/@when/@then` steps + `.feature` files |
| Concurrency | Real (`asyncio.gather()`) | Sequential (sync step functions) |
| Shared state | Local variables | `ScenarioContext` dataclass |
| `asyncio_mode` | `"auto"` (required) | Not used |
| Extra layers | None | pytest-bdd + Gherkin |
