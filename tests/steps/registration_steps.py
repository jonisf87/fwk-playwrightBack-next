"""
BDD step definitions for registration.feature.
TypeScript equivalent: tests/steps/Registration.steps.ts

KEY DIFFERENCES — Registration steps:

  1. SYNC API — no async/await (see login_steps.py for the full explanation).
     TS: response = await page.request.post(url, { data: {...} })
     PY: response = page.request.post(url, data={...})

  2. CRITICAL — response.status is a PROPERTY, not a method:
     TS: response.status()   — method call returning a number
     PY: response.status     — property (integer, no parentheses)
     Writing response.status() returns a bound method object — always truthy.
     This is the most common silent Playwright bug when porting from TypeScript.

  3. response.json() and response.text() are synchronous in sync_api:
     TS: const body = await response.json()   — async method
     PY: body = response.json()               — sync method (no await)

  4. Falsy check with 'or':
     TS: data.userName || data.username
     PY: data.get("userName") or data.get("username")
     Python's 'or' short-circuits just like JavaScript's '||'.

  5. f-strings replace string concatenation:
     TS: 'API registration failed: ' + JSON.stringify(body)
     PY: f"API registration failed: {body}"

NOTE: The Background steps (navigate_to_registration_page, fill_registration_valid,
  see_success_message) are defined in conftest.py, not here. This ensures they are
  registered in the global step registry before login_steps.py calls scenarios().
"""

import re

from faker import Faker
from playwright.sync_api import Page
from pytest_bdd import scenarios, then, when

from tests.conftest import _generate_username
from tests.pages.registration_page import RegistrationPage

scenarios("../features/registration.feature")

fake = Faker()
BASE_URL = "https://demoqa.com"

INVALID_PASSWORD = "password1!"  # no uppercase — triggers demoqa validation error


@when("I fill in the registration form with an invalid password")
def fill_registration_invalid_password(
    registration_page: RegistrationPage,
    page: Page,
) -> None:
    """
    Try UI registration first; fall back to API if CAPTCHA blocks the form.
    """
    first_name = fake.first_name()
    last_name = fake.last_name()
    username = _generate_username()

    registration_page.fill_first_name(first_name)
    registration_page.fill_last_name(last_name)
    registration_page.fill_username(username)
    registration_page.fill_password(INVALID_PASSWORD)
    registration_page.click_captcha_checkbox()
    registration_page.click_register()

    error = registration_page.get_error_message()

    if not error or "reCaptcha" in error:  # KEY DIFFERENCE: TS was !error || includes("reCaptcha")
        response = page.request.post(
            f"{BASE_URL}/Account/v1/User",
            data={"userName": username, "password": INVALID_PASSWORD},
            headers={"Content-Type": "application/json"},
        )
        if response.status in (400, 406):
            error = response.text()
        else:
            raise AssertionError(f"Expected API to reject invalid password, got {response.status}")

    registration_page._registration_error = error


@then("I should see a validation error message")
def see_validation_error(registration_page: RegistrationPage) -> None:
    """
    KEY DIFFERENCE — regex matching:
    TS: expect(error).toMatch(/Password must have|Passwords must have/i)
    PY: assert re.search(r"Password must have|Passwords must have", error, re.IGNORECASE)
    The /i flag in TS regex becomes re.IGNORECASE in Python.
    """
    error = getattr(registration_page, "_registration_error", None)
    if not error:
        error = registration_page.get_error_message()
    assert error is not None, "Expected a validation error, got None"
    assert re.search(r"Password must have|Passwords must have", error, re.IGNORECASE), f"Unexpected error: '{error}'"
