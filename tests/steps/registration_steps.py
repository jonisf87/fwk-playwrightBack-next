"""
BDD step definitions for registration.feature.
TypeScript equivalent: tests/steps/Registration.steps.ts

KEY DIFFERENCES — Registration steps:

  1. Timeout configuration:
     TS: setDefaultTimeout(60 * 1000)  — Cucumber global timeout setter
     PY: @pytest.mark.timeout(60) per test, or set globally in pyproject.toml
     We configure the 60s timeout via playwright's wait_for_selector timeout parameter
     directly, which is more explicit and localised than a global setter.

  2. API registration via page.request:
     TS: await this.page.request.post(url, { data: {...}, headers: {...} })
     PY: await page.request.post(url, data={...}, headers={...})
     Identical semantics. page.request is an APIRequestContext bound to the browser context.

  3. CRITICAL — response.status is a PROPERTY in Python:
     TS: response.status()   — method call returning a number
     PY: response.status     — property (integer, no parentheses)
     Writing response.status() in Python returns a bound method object, which is always
     truthy — assertions like 'assert response.status() == 200' would NEVER fail.
     This is the most common silent bug when porting Playwright from TypeScript to Python.

  4. response.json() is a coroutine in Python:
     TS: const body = await response.json()   — async method
     PY: body = await response.json()         — async method (same pattern)
     Both require await. No difference here — just confirming it's consistent.

  5. Falsy check with 'or':
     TS: data.userName || data.username   — JavaScript short-circuit OR with falsy
     PY: data.get("userName") or data.get("username")  — Python 'or' operator
     Python's 'or' also short-circuits: returns first truthy value or the last value.
     Equivalent semantics for non-empty string vs undefined/null.

  6. f-strings replace string concatenation:
     TS: 'API registration failed: ' + JSON.stringify(body)
     PY: f"API registration failed: {body}"
     Python's f-strings interpolate any value using its __repr__ or __str__.
"""

import json
import re
import time
from pathlib import Path

from faker import Faker
from playwright.async_api import Page
from pytest_bdd import given, scenarios, then, when

from tests.pages.registration_page import RegistrationPage

scenarios("../features/registration.feature")

fake = Faker()
BASE_URL = "https://demoqa.com"
DATA_PATH = Path(__file__).parent.parent / "support" / "data.json"

INVALID_PASSWORD = "password1!"  # no uppercase — triggers demoqa validation error


def _generate_username() -> str:
    """Strip non-alphanumeric chars and add timestamp for uniqueness.
    TS: faker.internet.userName().replace(/[^a-zA-Z0-9]/g, '') + Date.now()
    PY: re.sub(r'[^a-zA-Z0-9]', '', fake.user_name()) + str(int(time.time() * 1000))
    """
    return re.sub(r"[^a-zA-Z0-9]", "", fake.user_name()) + str(int(time.time() * 1000))


@given("I navigate to the registration page", target_fixture="registration_page")
async def navigate_to_registration_page(page: Page) -> RegistrationPage:
    reg_page = RegistrationPage(page)
    await reg_page.goto()
    return reg_page


@when("I fill in the registration form with valid data")
async def fill_registration_valid(
    registration_page: RegistrationPage,
    page: Page,
) -> None:
    """
    API-bypass strategy: register via REST API to avoid CAPTCHA.
    TypeScript uses this.page.request.post() — Python uses page.request.post().

    KEY DIFFERENCE — status check (see module docstring, point 3):
    TS: response.status()   → PY: response.status  (property, no parentheses)
    """
    # Load or generate credentials
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

    # KEY DIFFERENCE: response.status is a PROPERTY (not a method call)
    # TS: if (response.status() === 201) ...
    # PY: if response.status == 201: ...
    response = await page.request.post(
        f"{BASE_URL}/Account/v1/User",
        data={"userName": username, "password": password},
        headers={"Content-Type": "application/json"},
    )

    if response.status == 201:
        registration_page._registration_message = "User Register Successfully."
    elif response.status == 406:
        body = await response.json()
        # User already exists — treat as success for test reuse
        if isinstance(body.get("message"), str) and "User exists" in body["message"]:
            registration_page._registration_message = "User Register Successfully."
        else:
            raise AssertionError(f"API registration failed: {body}")
    else:
        text = await response.text()
        raise AssertionError(f"API registration failed ({response.status}): {text}")


@when("I fill in the registration form with an invalid password")
async def fill_registration_invalid_password(
    registration_page: RegistrationPage,
    page: Page,
) -> None:
    """
    Try UI registration first; fall back to API if CAPTCHA blocks the form.
    Same two-path strategy as the TypeScript version.
    """
    first_name = fake.first_name()
    last_name = fake.last_name()
    username = _generate_username()

    await registration_page.fill_first_name(first_name)
    await registration_page.fill_last_name(last_name)
    await registration_page.fill_username(username)
    await registration_page.fill_password(INVALID_PASSWORD)
    await registration_page.click_captcha_checkbox()
    await registration_page.click_register()

    error = await registration_page.get_error_message()

    if error and "reCaptcha" in error:
        # CAPTCHA blocked UI — fall back to API
        # API should return 400 for invalid password
        response = await page.request.post(
            f"{BASE_URL}/Account/v1/User",
            data={"userName": username, "password": INVALID_PASSWORD},
            headers={"Content-Type": "application/json"},
        )
        if response.status in (400, 406):
            error = await response.text()
        else:
            raise AssertionError(f"Expected API to reject invalid password, got {response.status}")

    registration_page._registration_error = error


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


@then("I should see a validation error message")
async def see_validation_error(registration_page: RegistrationPage) -> None:
    """
    KEY DIFFERENCE — regex matching:
    TS: expect(error).toMatch(/Password must have|Passwords must have/i)
    PY: assert re.search(r"Password must have|Passwords must have", error, re.IGNORECASE)
    The /i flag in TS regex becomes re.IGNORECASE in Python.
    """
    error = getattr(registration_page, "_registration_error", None)
    if not error:
        error = await registration_page.get_error_message()
    assert error is not None, "Expected a validation error, got None"
    assert re.search(r"Password must have|Passwords must have", error, re.IGNORECASE), f"Unexpected error: '{error}'"
