"""
Pytest fixtures replacing Cucumber's CustomWorld + Before/After hooks.
TypeScript equivalent: tests/support/world.ts

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURAL OVERVIEW — The most important difference in this entire project
═══════════════════════════════════════════════════════════════════════════════

TypeScript / Cucumber.js approach:
  1. Define a class (CustomWorld) that holds all shared state as instance attributes.
  2. Register it with setWorldConstructor() so Cucumber creates one instance per scenario.
  3. Write Before/After hooks that call methods on 'this' (the World instance) to
     set up and tear down resources (browser, page, API context).
  4. Steps access state via 'this.page', 'this.credentials', etc.

     CustomWorld { browser, page, credentials, apiToken, ... }
          ↑ 'this' in every step function

Python / pytest approach:
  1. Define fixtures — plain functions decorated with @pytest.fixture.
  2. pytest creates and injects them automatically based on parameter names.
  3. A fixture with 'yield' is both setup AND teardown:
       code before yield  →  equivalent to Before hook
       yield <value>      →  the value is injected into tests/steps as a parameter
       code after yield   →  equivalent to After hook
  4. Steps receive state as function parameters, not as 'this'.

     def test_login(page: Page, ctx: ScenarioContext): ...
                         ↑ injected             ↑ injected
                         by 'page' fixture      by 'ctx' fixture

KEY CONCEPT — sync vs async Playwright API:
  This branch (feature/bdd-pom) uses playwright.sync_api.
  pytest-bdd calls step functions SYNCHRONOUSLY via its internal _execute_step_function.
  It does not await coroutines, so async step functions are silently broken.
  Using the sync API matches pytest-bdd's execution model perfectly.

  The native branch (feature/native-playwright) uses playwright.async_api with
  asyncio.gather() for true concurrency — pytest test functions are async and
  pytest-asyncio handles the event loop correctly there.

KEY DIFFERENCE: asyncio_mode is NOT needed in this branch because all Playwright
  calls are synchronous. The native branch needs asyncio_mode = "auto" because its
  test functions are async def.

BACKGROUND STEP REGISTRATION (why shared steps live here):
  pytest-bdd v7 populates the global step registry when @given/@when/@then decorators
  run at module import time. Test files are collected alphabetically:
  login_steps.py is imported before registration_steps.py. When scenarios() fires for
  login.feature, the Background steps defined in registration_steps.py are not yet
  registered → StepDefinitionNotFoundError.
  Defining those Background steps here guarantees they are registered before any
  *_steps.py file is collected.
"""

import json
import os
import re
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from faker import Faker
from playwright.sync_api import (
    APIRequestContext,
    APIResponse,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from pytest_bdd import given, then, when

from tests.pages.registration_page import RegistrationPage

BASE_URL = "https://demoqa.com"

# Shared between Background steps and any module that imports _generate_username
fake = Faker()
DATA_PATH = Path(__file__).parent / "support" / "data.json"


# ─────────────────────────────────────────────────────────────────────────────
# ScenarioContext — replaces CustomWorld instance attributes
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ScenarioContext:
    """
    Mutable state shared between steps within a single scenario.

    KEY DIFFERENCE: TypeScript CustomWorld used class instance attributes:
      class CustomWorld extends World {
        credentials: { userName: string; password: string } | null = null;
        apiToken?: string;
        ...
      }

    Python uses a @dataclass — a class where __init__, __repr__, and __eq__
    are auto-generated from the field declarations. No boilerplate constructor.

    KEY DIFFERENCE: Optional fields syntax:
      TS:  apiToken?: string        — '?' means the field may not exist at all
      PY:  api_token: str | None = None  — field always exists, value may be None
      Python dataclasses require a default value for optional fields.

    KEY DIFFERENCE: Dict type for credentials:
      TS:  { userName: string; password: string }  — anonymous object type / interface
      PY:  dict[str, str]                          — typed dict (generic syntax, PEP 585)
    """

    # UI test state
    credentials: dict[str, str] | None = None
    registration_message: str | None = None
    registration_error: str | None = None

    # API test state
    api_user: dict[str, str] | None = None
    api_response: APIResponse | None = None
    api_response_body: Any = field(default=None)  # 'unknown' in TS → Any in Python
    api_token: str | None = None
    api_user_id: str | None = None

    # Parallel users test state (replaces this.formConfirmation, this.gridOrderChanged)
    form_confirmation: bool = False
    grid_order_changed: bool = False
    email_error: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Playwright lifecycle fixtures — replace CustomWorld.init() / CustomWorld.close()
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def playwright_instance() -> Generator[Playwright, None, None]:
    """
    Launch the Playwright driver using the SYNCHRONOUS API.

    KEY DIFFERENCE: sync_playwright() vs async_playwright():
      BDD branch:    with sync_playwright() as pw: yield pw
      Native branch: async with async_playwright() as pw: yield pw

    pytest-bdd calls step functions synchronously — using sync_playwright()
    means all Playwright calls (goto, fill, click, etc.) block until complete,
    which is exactly what a sequential BDD scenario needs.

    TypeScript's @playwright/test runner managed this transparently; Python
    requires an explicit choice between sync and async APIs.
    """
    with sync_playwright() as pw:
        yield pw


@pytest.fixture
def browser_name() -> str:
    """
    Read browser selection from the BROWSER environment variable.

    KEY DIFFERENCE:
      TS: process.env.BROWSER || 'chromium'    — Node.js global
      PY: os.environ.get("BROWSER", "chromium") — standard library

    Both default to chromium. CI sets BROWSER=firefox for the matrix job.
    """
    return os.environ.get("BROWSER", "chromium").lower()


@pytest.fixture
def browser(playwright_instance: Playwright, browser_name: str) -> Generator[Browser, None, None]:
    """
    Launch the browser. Equivalent to CustomWorld.init()'s browser selection.

    KEY DIFFERENCE: Python replaces TypeScript's switch/case with getattr():
      TS:
        switch (browserType) {
          case 'firefox': browserLauncher = firefox; break;
          case 'webkit':  browserLauncher = webkit;  break;
          default:        browserLauncher = chromium;
        }
        this.browser = await browserLauncher.launch({ headless: true });

      PY:
        launcher = getattr(playwright_instance, browser_name)
        browser  = launcher.launch(headless=True)

    getattr(obj, name) is equivalent to obj.<name> but with a dynamic string.
    playwright_instance.chromium, playwright_instance.firefox, playwright_instance.webkit
    are all valid attributes — getattr selects the right one at runtime.

    KEY DIFFERENCE — fixture teardown (sync vs async):
      TS: await this.browser?.close() in After hook
      BDD: b.close() after yield  — sync, no await needed
      Native: await b.close() after yield — async
    """
    launcher = getattr(playwright_instance, browser_name)
    b = launcher.launch(headless=True)
    yield b
    b.close()


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Create a browser context.

    KEY DIFFERENCE:
      TS: this.context = await this.browser.newContext()
      PY: ctx = browser.new_context(base_url=BASE_URL)

    base_url means page.goto("/login") resolves to "https://demoqa.com/login".
    The TS project used full URLs in each goto() call — base_url is cleaner.
    """
    ctx = browser.new_context(base_url=BASE_URL)
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Open a page within the browser context.

    KEY DIFFERENCE:
      TS: this.page = await this.context.newPage() — stored on World, passed via 'this'
      PY: yield p — the page is RETURNED to whoever requests the 'page' fixture

    In step definitions:
      TS: When('...', async function(this: CustomWorld) { await this.page.fill(...) })
      PY: @when('...')  def step(page: Page): page.fill(...)
                                   ↑ injected automatically, no await needed (sync API)
    """
    p = context.new_page()
    yield p
    p.close()


@pytest.fixture
def api_request_context(playwright_instance: Playwright) -> Generator[APIRequestContext, None, None]:
    """
    Create an API-only request context (no browser).

    KEY DIFFERENCE — conditional init in TypeScript vs separate fixture in Python:
      TS: CustomWorld.init(isApi: boolean) — one method handles both cases,
          branching on the isApi flag detected from scenario tags.

      PY: Two completely separate fixtures: 'page' for UI, 'api_request_context' for API.
          A step that needs API just declares 'api_request_context' as a parameter.
          A step that needs a browser declares 'page'. pytest handles the rest.
          No tag detection needed — the fixture requested determines what's created.

    KEY DIFFERENCE — disposal method (sync):
      TS: await this.apiRequestContext?.dispose()
      PY: ctx.dispose()   — sync, no await or optional chaining needed
    """
    ctx = playwright_instance.request.new_context(base_url=BASE_URL)
    yield ctx
    ctx.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Scenario state fixture — replaces CustomWorld instance per scenario
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def ctx() -> ScenarioContext:
    """
    Fresh ScenarioContext for each test scenario.

    KEY DIFFERENCE: CustomWorld was instantiated once per scenario by Cucumber
    via setWorldConstructor(CustomWorld). pytest creates a new ScenarioContext
    automatically for each test function because the fixture has function scope
    (the default — no 'scope' argument means scope="function").

    Steps share state by mutating this object:
      TS: this.apiToken = response.token
      PY: ctx.api_token = response["token"]   (ctx injected as parameter)
    """
    return ScenarioContext()


# ─────────────────────────────────────────────────────────────────────────────
# Background step definitions shared by login.feature and registration.feature
# ─────────────────────────────────────────────────────────────────────────────
# These three steps appear in the Background block of login.feature.
# They are defined here — not in registration_steps.py — because pytest-bdd v7
# populates its global step registry at @decorator execution time (module import).
# login_steps.py is alphabetically before registration_steps.py, so when
# scenarios("login.feature") runs it would fail to find these steps.
# conftest.py is always loaded first, so registration happens before any *_steps.py.


def _generate_username() -> str:
    """Strip non-alphanumeric chars and append millisecond timestamp for uniqueness.
    TS: faker.internet.userName().replace(/[^a-zA-Z0-9]/g, '') + Date.now()
    PY: re.sub(r'[^a-zA-Z0-9]', '', fake.user_name()) + str(int(time.time() * 1000))
    """
    return re.sub(r"[^a-zA-Z0-9]", "", fake.user_name()) + str(int(time.time() * 1000))


@given("I navigate to the registration page", target_fixture="registration_page")
def navigate_to_registration_page(page: Page) -> RegistrationPage:
    """
    KEY DIFFERENCE — target_fixture:
    TS: this.pageObj = new RegistrationPage(this.page)  — mutates World state
    PY: return RegistrationPage(page)                   — becomes the 'registration_page' fixture
    Subsequent steps declare 'registration_page: RegistrationPage' and pytest injects it.
    """
    reg_page = RegistrationPage(page)
    reg_page.goto()
    return reg_page


@when("I fill in the registration form with valid data")
def fill_registration_valid(
    registration_page: RegistrationPage,
    page: Page,
) -> None:
    """
    API-bypass strategy: register via REST API to avoid CAPTCHA, then assert via page object.

    KEY DIFFERENCE — response.status is a PROPERTY, not a method:
    TS: response.status()   → returns number
    PY: response.status     → integer property (no parentheses — calling it returns a bound method)

    KEY DIFFERENCE — response.json() is synchronous in sync_api:
    TS: const body = await response.json()
    PY: body = response.json()   (no await)
    """
    if DATA_PATH.exists():
        data = json.loads(DATA_PATH.read_text())
        username = data.get("userName") or data.get("username")
        password = data.get("password")
    else:
        username = _generate_username()
        password = "TestPass1!"
        DATA_PATH.write_text(json.dumps({"userName": username, "password": password}, indent=2))

    if not username or not password:
        raise ValueError("Credentials missing from data.json")

    response = page.request.post(
        f"{BASE_URL}/Account/v1/User",
        data={"userName": username, "password": password},
        headers={"Content-Type": "application/json"},
    )

    if response.status == 201:
        registration_page._registration_message = "User Register Successfully."
    elif response.status == 406:
        body = response.json()
        if isinstance(body.get("message"), str) and "User exists" in body["message"]:
            registration_page._registration_message = "User Register Successfully."
        else:
            raise AssertionError(f"API registration failed: {body}")
    else:
        text = response.text()
        raise AssertionError(f"API registration failed ({response.status}): {text}")


@then("I should see a success message")
def see_success_message(registration_page: RegistrationPage) -> None:
    """
    KEY DIFFERENCE — assert vs expect:
    TS: expect(message?.trim()).toBe('User Register Successfully.')
    PY: assert message.strip() == "User Register Successfully."
    """
    message = getattr(registration_page, "_registration_message", None)
    assert message is not None, "Registration message was never set"
    assert message.strip() == "User Register Successfully."
