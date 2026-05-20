"""
Registration tests using pytest-playwright (sync).
"""

import re
import time

import pytest
from playwright.sync_api import APIRequestContext

BASE_URL = "https://demoqa.com"
INVALID_PASSWORD = "password1!"


@pytest.mark.api
def test_registration_with_valid_data(api_request_context: APIRequestContext) -> None:
    username = f"testuser{int(time.time() * 1000)}"
    response = api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data={"userName": username, "password": "TestPass1!"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status in (201, 406)
    if response.status == 406:
        body = response.json()
        assert "User exists" in body.get("message", "")


@pytest.mark.api
def test_registration_rejects_invalid_password(api_request_context: APIRequestContext) -> None:
    username = f"testuser{int(time.time() * 1000)}"
    response = api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data={"userName": username, "password": INVALID_PASSWORD},
        headers={"Content-Type": "application/json"},
    )
    assert response.status == 400
    body = response.json()
    message = body.get("message", "") if isinstance(body, dict) else ""
    assert re.search(r"Password must have|Passwords must have", message, re.IGNORECASE)
