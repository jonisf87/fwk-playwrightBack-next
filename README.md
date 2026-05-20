# Playwright Python Framework (feature/bdd-pom branch)

End-to-end testing framework for [demoqa.com](https://demoqa.com) built with Python, Playwright, and pytest. This branch demonstrates the **BDD approach**: scenarios written in plain English using Gherkin syntax, with Python step definitions underneath, and Page Objects handling the browser interaction.

If you come from TypeScript, think of this branch as the Python equivalent of Cucumber.js + POM. The other branch (`feature/native-playwright`) is the equivalent of writing tests directly with `@playwright/test`.

---

## What is BDD and why does it matter here?

BDD stands for Behaviour-Driven Development. Instead of writing test functions like `test_login_works()`, you write scenarios in a language called Gherkin that anyone (developers, testers, product managers) can read:

```gherkin
Scenario: Successful login with valid credentials
  Given I navigate to the login page
  When I fill in the login form with valid stored credentials
  Then I should see my profile page
```

Each line (`Given`, `When`, `Then`) maps to a Python function called a **step definition**. The test runner (`pytest-bdd`) connects the Gherkin text to the right Python function automatically.

---

## The most important architectural difference

In TypeScript/Cucumber, shared state between steps lives on `this` (a `CustomWorld` class instance). In Python/pytest-bdd, there is no `this`. Instead, shared state is passed as function parameters (called **fixtures**).

```python
# TypeScript (Cucumber.js) — state lives on 'this'
When('I request a token', async function(this: CustomWorld) {
    this.apiToken = await getToken()
})

# Python (pytest-bdd) — state lives in a dataclass passed as a parameter
@when("I request a token")
def request_token(ctx: ScenarioContext) -> None:
    ctx.api_token = get_token()
```

`ScenarioContext` is a simple dataclass defined in `conftest.py` that replaces the `CustomWorld` class. A fresh instance is created for every scenario automatically.

---

## Why sync_api instead of async_api?

This branch uses `playwright.sync_api` (no `async/await` anywhere). The reason: `pytest-bdd` calls step functions **synchronously** via its internal `_execute_step_function`. If a step function is `async def`, pytest-bdd creates the coroutine but never awaits it, so the step body silently never runs.

The sync API means every Playwright call blocks until complete, which matches how pytest-bdd executes steps sequentially. The native branch (`feature/native-playwright`) uses `async_api` with `asyncio.gather()` for true concurrency.

---

## Project structure

```
tests/
├── conftest.py               # ScenarioContext dataclass + Playwright fixtures (sync)
├── features/
│   ├── login.feature         # Gherkin scenarios for login
│   ├── registration.feature  # Gherkin scenarios for registration
│   ├── parallel_users.feature# Gherkin scenarios for multi-user interaction
│   └── api.feature           # Gherkin scenarios for REST API calls
├── steps/
│   ├── login_steps.py        # step definitions for login.feature
│   ├── registration_steps.py # step definitions for registration.feature
│   ├── parallel_users_steps.py# step definitions for parallel_users.feature
│   └── api_steps.py          # step definitions for api.feature
├── pages/
│   ├── login_page.py         # Page Object for demoqa.com/login (sync)
│   ├── registration_page.py  # Page Object for demoqa.com/register (sync)
│   ├── practice_form_page.py # Page Object for the practice form (sync)
│   └── sortable_page.py      # Page Object for demoqa.com/sortable (sync)
├── fixtures/
│   └── test-image.png        # image file used in the file upload test
└── support/
    ├── generate_data.py      # generates test credentials and writes them to data.json
    └── data.json             # persisted credentials (git-ignored)
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

# Verbose output showing each scenario step
pytest tests/ -v

# One specific scenario
pytest tests/steps/login_steps.py::test_successful_login_with_valid_credentials -v

# Collect only (show which tests would run without running them)
pytest tests/ --collect-only
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

**`@pytest.fixture` with `yield` replaces Cucumber Before/After hooks**
The code before `yield` is the setup (equivalent to a `Before` hook). The code after `yield` is the teardown (equivalent to an `After` hook). pytest creates one fixture instance per test function (scenario) by default.

```python
@pytest.fixture
def browser(playwright_instance, browser_name):
    b = playwright_instance.chromium.launch(headless=True)
    yield b          # test runs here
    b.close()        # teardown runs after the test
```

**`target_fixture` turns a `@given` step into a named fixture**
When a step needs to return a value for later steps to use, add `target_fixture="name"`. The return value becomes a fixture named `"name"` that subsequent steps can request as a parameter.

```python
@given("I navigate to the login page", target_fixture="login_page")
def navigate(page: Page) -> LoginPage:
    return LoginPage(page)   # now 'login_page' is available to all following steps
```

**Why Background steps live in `conftest.py`**
pytest-bdd v7 registers step definitions in a global dictionary when the `@given/@when/@then` decorators run (at import time). Files are collected alphabetically: `login_steps.py` is imported before `registration_steps.py`. When `login_steps.py` calls `scenarios("login.feature")`, the Background steps defined in `registration_steps.py` are not yet registered, causing a `StepDefinitionNotFoundError`. Putting those steps in `conftest.py` guarantees they are registered before any `*_steps.py` file is imported.

**`response.status` is a property, not a method**
The most common mistake when porting from TypeScript: in TS you write `response.status()` (method call), in Python it is `response.status` (integer property). Writing `response.status()` in Python returns a bound method object, which is always truthy, so assertions never fail even on 404 or 500 responses.

**`f.url` is a property on Frame objects**
In TypeScript, `frame.url()` is a method call. In Python, `frame.url` is a property (no parentheses). Writing `frame.url()` returns a bound method and the string comparison always fails silently.

**`page.evaluate("() => { ... }")` receives a JS string**
In TypeScript you can pass a real arrow function. In Python the argument must be a string containing JavaScript source code. `page.evaluate(lambda: ...)` does not work.

---

## CI/CD

The workflow `.github/workflows/bdd-pom.yml` runs three jobs:

```
lint  →  ui-tests (chromium + firefox, in parallel)
      →  api-tests
```

UI tests only run if lint passes first. API tests and UI tests run in parallel with each other.

---

## Comparison with feature/native-playwright

| Aspect | This branch (BDD) | Native branch |
|---|---|---|
| Playwright API | `sync_api` (no await) | `async_api` (await everywhere) |
| Test format | `.feature` files + step definitions | `async def test_*` functions |
| Concurrency | Sequential (sync step functions) | Real (`asyncio.gather()`) |
| Shared state | `ScenarioContext` dataclass | Local variables |
| `asyncio_mode` | Not used | `"auto"` (required) |
| Extra layers | pytest-bdd + Gherkin | None |
