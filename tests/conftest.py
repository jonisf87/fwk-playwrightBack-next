"""
pytest-playwright conftest for feature/native-playwright-reports.

KEY DIFFERENCE vs feature/native-playwright:
  That branch manages the full Playwright lifecycle manually (async_playwright,
  Browser, BrowserContext, Page as async fixtures). This branch delegates all of
  that to pytest-playwright, which provides the same fixtures out of the box —
  plus screenshot, trace, and video capture with zero extra code.

  native-playwright         →  feature/native-playwright-reports
  ─────────────────────────────────────────────────────────────
  async def playwright_instance()   →  (provided by pytest-playwright)
  async def browser()               →  (provided by pytest-playwright)
  async def context()               →  (provided by pytest-playwright)
  async def page()                  →  (provided by pytest-playwright)
  async def api_request_context()   →  defined here (removed from pytest-playwright 0.5+)
  asyncio_mode = "auto"             →  not needed (sync API)
  asyncio.gather() concurrency      →  sequential (two contexts, one after the other)

pytest-playwright fixture reference:
  https://playwright.dev/python/docs/test-runners#fixtures

Artifacts are configured in pyproject.toml [tool.pytest.ini_options]:
  addopts = "--screenshot=only-on-failure --tracing=retain-on-failure"

Artifacts land in test-results/<test-name>/ and can be opened with:
  playwright show-trace test-results/<name>/trace.zip
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

BASE_URL = "https://demoqa.com"


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Override pytest-playwright's base_url fixture.
    All page.goto("/path") calls resolve to https://demoqa.com/path.
    Equivalent to playwright.config.ts { use: { baseURL: 'https://demoqa.com' } }.
    """
    return BASE_URL


@pytest.fixture(scope="session")
def api_request_context(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    """
    Standalone HTTP client, no browser required.
    pytest-playwright removed this built-in fixture in v0.5+; we recreate it here.
    Equivalent to TypeScript's request.newContext({ baseURL }) in a global setup file.
    """
    ctx = playwright.request.new_context(base_url=BASE_URL)
    yield ctx
    ctx.dispose()
