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

KEY CONCEPT: pytest's dependency injection resolves fixtures by PARAMETER NAME.
If a function has a parameter named 'page', pytest finds the fixture named 'page'
and calls it. This is why setWorldConstructor() is not needed — pytest wires
dependencies automatically at call time.
"""

import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

import pytest
from playwright.async_api import (
    APIRequestContext,
    APIResponse,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

BASE_URL = "https://demoqa.com"


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
async def playwright_instance() -> AsyncGenerator[Playwright, None]:
    """
    Launch the Playwright driver.

    KEY DIFFERENCE: Playwright in Python is used as an async context manager.
      TS: (implicitly managed by @playwright/test runner)
      PY: async with async_playwright() as pw: yield pw

    'async with' ensures __aenter__ and __aexit__ are called correctly.
    The 'yield' inside an async context manager is valid Python — the fixture
    stays alive (inside the 'with' block) for the duration of the test.
    """
    async with async_playwright() as pw:
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
async def browser(playwright_instance: Playwright, browser_name: str) -> AsyncGenerator[Browser, None]:
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
        browser  = await launcher.launch(headless=True)

    getattr(obj, name) is equivalent to obj.<name> but with a dynamic string.
    playwright_instance.chromium, playwright_instance.firefox, playwright_instance.webkit
    are all valid attributes — getattr selects the right one at runtime.

    KEY DIFFERENCE — fixture teardown:
      TS: await this.browser?.close() in After hook
      PY: await b.close() after yield — runs automatically when the test ends
    """
    launcher = getattr(playwright_instance, browser_name)
    b = await launcher.launch(headless=True)
    yield b
    await b.close()  # ← After hook equivalent — runs after test completes


@pytest.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """
    Create a browser context.

    KEY DIFFERENCE:
      TS: this.context = await this.browser.newContext()
      PY: ctx = await browser.new_context(base_url=BASE_URL)

    base_url means page.goto("/login") resolves to "https://demoqa.com/login".
    The TS project used full URLs in each goto() call — base_url is cleaner.
    """
    ctx = await browser.new_context(base_url=BASE_URL)
    yield ctx
    await ctx.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """
    Open a page within the browser context.

    KEY DIFFERENCE:
      TS: this.page = await this.context.newPage() — stored on World, passed via 'this'
      PY: yield p — the page is RETURNED to whoever requests the 'page' fixture

    In step definitions:
      TS: When('...', async function(this: CustomWorld) { await this.page.fill(...) })
      PY: @when('...')  async def step(page: Page): await page.fill(...)
                                            ↑ injected automatically
    """
    p = await context.new_page()
    yield p
    await p.close()


@pytest.fixture
async def api_request_context(playwright_instance: Playwright) -> AsyncGenerator[APIRequestContext, None]:
    """
    Create an API-only request context (no browser).

    KEY DIFFERENCE — conditional init in TypeScript vs separate fixture in Python:
      TS: CustomWorld.init(isApi: boolean) — one method handles both cases,
          branching on the isApi flag detected from scenario tags.

      PY: Two completely separate fixtures: 'page' for UI, 'api_request_context' for API.
          A step that needs API just declares 'api_request_context' as a parameter.
          A step that needs a browser declares 'page'. pytest handles the rest.
          No tag detection needed — the fixture requested determines what's created.

    KEY DIFFERENCE — disposal method:
      TS: await this.apiRequestContext?.dispose()   — optional chaining (?.) for null safety
      PY: await ctx.dispose()                       — fixture is guaranteed non-None here
    """
    ctx = await playwright_instance.request.new_context(base_url=BASE_URL)
    yield ctx
    await ctx.dispose()


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
