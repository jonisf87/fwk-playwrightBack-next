"""
Native Playwright registration tests — no BDD/Gherkin layer.
BDD branch equivalent: tests/features/registration.feature + tests/steps/registration_steps.py

KEY DIFFERENCE — API-bypass for CAPTCHA:
  demoqa.com shows a reCAPTCHA on the registration form.
  Automated browsers cannot solve reCAPTCHA interactively.
  Both branches use the same workaround: POST directly to the REST API
  to register the user, bypassing the UI form entirely.

  This is a common real-world pattern: test the UI flow for the happy path,
  use the API for test setup that would be blocked by anti-bot measures.

KEY DIFFERENCE — response.status PROPERTY:
  TS: response.status()  → method call, returns number
  PY: response.status    → integer property (no parentheses)
  Writing response.status() in Python returns a bound method — always truthy.
  This is the #1 Playwright porting bug from TypeScript to Python.
"""

import re
import time

import pytest
from playwright.async_api import APIRequestContext

BASE_URL = "https://demoqa.com"
INVALID_PASSWORD = "password1!"  # no uppercase — fails demoqa validation


@pytest.mark.api
async def test_registration_with_valid_data(api_request_context: APIRequestContext) -> None:
    """
    Register via REST API. Status 201 = created, 406 = user already exists.

    KEY DIFFERENCE — await response.json() in async_api:
      BDD:    body = response.json()        (sync, no await)
      Native: body = await response.json()  (async coroutine)
    """
    username = f"testuser{int(time.time() * 1000)}"
    response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data={"userName": username, "password": "TestPass1!"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status in (201, 406), f"Unexpected status: {response.status}"
    if response.status == 406:
        body = await response.json()
        assert "User exists" in body.get("message", ""), f"Unexpected 406 body: {body}"


@pytest.mark.api
async def test_registration_rejects_invalid_password(api_request_context: APIRequestContext) -> None:
    """
    demoqa requires: uppercase, lowercase, digit, special char.
    'password1!' has no uppercase → API returns 400.

    KEY DIFFERENCE — isinstance() vs typeof:
      TS: typeof body.message === 'string'
      PY: isinstance(body.get("message"), str)
    """
    username = f"testuser{int(time.time() * 1000)}"
    response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data={"userName": username, "password": INVALID_PASSWORD},
        headers={"Content-Type": "application/json"},
    )
    assert response.status == 400, f"Expected 400 for invalid password, got {response.status}"
    body = await response.json()
    message = body.get("message", "") if isinstance(body, dict) else ""
    assert re.search(r"Password must have|Passwords must have", message, re.IGNORECASE), (
        f"Unexpected error message: '{message}'"
    )
