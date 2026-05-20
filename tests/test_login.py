"""
Login tests using pytest-playwright (sync).

KEY DIFFERENCE vs feature/native-playwright:
  That branch: async def test_* + await page.goto(...)
  This branch:      def test_* +       page.goto(...)

pytest-playwright automatically takes a screenshot if --screenshot=only-on-failure
is set in pyproject.toml, and saves a trace if --tracing=retain-on-failure.
No extra code needed — the plugin handles it transparently.
"""

import json
import re
import time
from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext, Page

from tests.pages.login_page import LoginPage

BASE_URL = "https://demoqa.com"
DATA_PATH = Path(__file__).parent / "support" / "data.json"


def _ensure_credentials(api_request_context: APIRequestContext) -> dict[str, str]:
    if DATA_PATH.exists():
        data = json.loads(DATA_PATH.read_text())
        username = data.get("userName") or data.get("username")
        password = data.get("password")
        if username and password:
            return {"userName": username, "password": password}

    username = re.sub(r"[^a-zA-Z0-9]", "", f"user{int(time.time() * 1000)}")
    password = "TestPass1!"
    credentials = {"userName": username, "password": password}
    response = api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    assert response.status in (201, 406), f"Registration failed: {response.status}"
    DATA_PATH.write_text(json.dumps(credentials, indent=2))
    return credentials


@pytest.mark.ui
def test_login_with_valid_credentials(page: Page, api_request_context: APIRequestContext) -> None:
    credentials = _ensure_credentials(api_request_context)
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login(credentials["userName"], credentials["password"])
    assert login_page.is_logged_in(), "Profile page not visible after login"


@pytest.mark.ui
def test_login_with_invalid_credentials(page: Page) -> None:
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login("invalidUser", "invalidPass")
    error = login_page.get_error_message()
    assert error is not None
    assert re.search(r"invalid|not match", error.lower()), f"Unexpected error: '{error}'"
