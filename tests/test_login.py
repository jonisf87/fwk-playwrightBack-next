"""
Native Playwright login tests — no BDD/Gherkin layer.
BDD branch equivalent: tests/features/login.feature + tests/steps/login_steps.py

KEY DIFFERENCES vs BDD branch:

  1. No Background block — setup is a plain async helper function or fixture.
     BDD: Background: Given/When/Then in the .feature file
     Native: async def _register_and_get_credentials() called at the top of each test.

  2. No ScenarioContext — state is local variables within the test function.
     BDD:    ctx.credentials = {...}  (mutates shared state object)
     Native: credentials = {...}      (local variable, no shared state needed)

  3. Test structure maps to: Arrange → Act → Assert (AAA pattern).
     BDD maps to: Given (Arrange) → When (Act) → Then (Assert).
     Both express the same intent; AAA is idiomatic for unit/integration tests.
"""

import json
import re
import time
from pathlib import Path

import pytest
from playwright.async_api import APIRequestContext, Page

from tests.pages.login_page import LoginPage

BASE_URL = "https://demoqa.com"
DATA_PATH = Path(__file__).parent / "support" / "data.json"


async def _ensure_credentials(api_request_context: APIRequestContext) -> dict[str, str]:
    """Register a user via API (CAPTCHA-free) and persist credentials to data.json."""
    if DATA_PATH.exists():
        data = json.loads(DATA_PATH.read_text())
        username = data.get("userName") or data.get("username")
        password = data.get("password")
        if username and password:
            return {"userName": username, "password": password}

    username = re.sub(r"[^a-zA-Z0-9]", "", f"user{int(time.time() * 1000)}")
    password = "TestPass1!"
    credentials = {"userName": username, "password": password}

    response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    assert response.status in (201, 406), f"Registration failed: {response.status}"
    DATA_PATH.write_text(json.dumps(credentials, indent=2))
    return credentials


@pytest.mark.ui
async def test_login_with_valid_credentials(page: Page, api_request_context: APIRequestContext) -> None:
    """
    Arrange: register user via API.
    Act:     fill login form and submit.
    Assert:  profile page is visible.

    KEY DIFFERENCE — await on every Playwright call:
    BDD:    login_page.goto()  /  login_page.login(u, p)   (sync)
    Native: await login_page.goto()  /  await login_page.login(u, p)
    """
    credentials = await _ensure_credentials(api_request_context)

    login_page = LoginPage(page)
    await login_page.goto()
    await login_page.login(credentials["userName"], credentials["password"])

    assert await login_page.is_logged_in(), "Profile page not visible after login"


@pytest.mark.ui
async def test_login_with_invalid_credentials(page: Page) -> None:
    login_page = LoginPage(page)
    await login_page.goto()
    await login_page.login("invalidUser", "invalidPass")

    error = await login_page.get_error_message()
    assert error is not None, "Expected a login error message"
    assert re.search(r"invalid|not match", error.lower()), f"Unexpected error: '{error}'"
