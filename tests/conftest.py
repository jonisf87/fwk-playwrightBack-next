"""
Async pytest fixtures for the native Playwright branch.

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURAL CONTRAST — native branch vs BDD branch
═══════════════════════════════════════════════════════════════════════════════

BDD branch (feature/bdd-pom):
  - playwright.sync_api  — all Playwright calls block, no await
  - pytest-bdd + Gherkin — scenarios() + @given/@when/@then
  - ScenarioContext dataclass — replaces CustomWorld instance attributes
  - Before/After via @pytest.fixture yield — replaces Cucumber hooks
  - Step functions are sync def — matches pytest-bdd's sync execution model
  - NO asyncio_mode needed

Native branch (feature/native-playwright):
  - playwright.async_api  — all Playwright calls must be awaited
  - Pure pytest  — test_*.py functions, no Gherkin layer
  - No shared state object — test functions receive fixtures directly
  - asyncio_mode = "auto" in pyproject.toml — pytest-asyncio runs every
    async def test_* as a coroutine on a fresh event loop
  - asyncio.gather() enables TRUE concurrent execution across contexts

KEY DIFFERENCE — async_playwright() context manager:
  BDD:    with sync_playwright() as pw: yield pw
  Native: async with async_playwright() as pw: yield pw
          ↑ 'async with' because __aenter__/__aexit__ are coroutines

KEY DIFFERENCE — fixture teardown:
  BDD:    b.close()        (sync, no await)
  Native: await b.close()  (must await — returns a coroutine)

KEY DIFFERENCE — why asyncio_mode = "auto":
  pytest-asyncio detects async def test_* functions and wraps them in
  asyncio.run() automatically. Without this, async tests are collected but
  their bodies never execute (the coroutine is created but not awaited).
  The BDD branch does NOT set this because all its step functions are sync.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from playwright.async_api import (
    APIRequestContext,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

BASE_URL = "https://demoqa.com"


@pytest.fixture
async def playwright_instance() -> AsyncGenerator[Playwright, None]:
    """
    Launch async Playwright driver.

    KEY DIFFERENCE — async context manager:
      BDD:    with sync_playwright() as pw: yield pw
      Native: async with async_playwright() as pw: yield pw
    """
    async with async_playwright() as pw:
        yield pw


@pytest.fixture
def browser_name() -> str:
    return os.environ.get("BROWSER", "chromium").lower()


@pytest.fixture
async def browser(playwright_instance: Playwright, browser_name: str) -> AsyncGenerator[Browser, None]:
    """
    KEY DIFFERENCE — await launch() and await close():
      BDD:    b = launcher.launch(headless=True)  /  b.close()
      Native: b = await launcher.launch(headless=True)  /  await b.close()
    """
    launcher = getattr(playwright_instance, browser_name)
    b = await launcher.launch(headless=True)
    yield b
    await b.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    ctx = await browser.new_context(base_url=BASE_URL)
    yield ctx
    await ctx.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """
    KEY DIFFERENCE — yield value and teardown both require await:
      BDD:    p = context.new_page()  /  p.close()
      Native: p = await context.new_page()  /  await p.close()
    """
    p = await context.new_page()
    yield p
    await p.close()


@pytest.fixture
async def api_request_context(playwright_instance: Playwright) -> AsyncGenerator[APIRequestContext, None]:
    ctx = await playwright_instance.request.new_context(base_url=BASE_URL)
    yield ctx
    await ctx.dispose()
