"""
BDD step definitions for login.feature.
TypeScript equivalent: tests/steps/Login.steps.ts

KEY DIFFERENCES — Step definitions:

  1. Global step registry vs explicit binding:
     TS (Cucumber): steps are auto-discovered from any required file; no per-file binding.
     PY (pytest-bdd): scenarios("../features/login.feature") explicitly registers all
     scenarios in this file as pytest test functions. Without this call, the scenarios
     are never collected. This is more explicit but requires one extra line per feature.

  2. 'this' context vs fixture injection:
     TS: Given('...', async function (this: CustomWorld) { this.pageObj = new LoginPage(...) })
     PY: @given("...", target_fixture="login_page")
         async def _(page: Page) -> LoginPage: return LoginPage(page)
     The return value of a @given with target_fixture becomes a named fixture available
     to all subsequent steps in the same scenario — no 'this' object, pure functions.

  3. isinstance() guard removed:
     TS: if (this.pageObj instanceof LoginPage) { ... } else { throw Error(...) }
     PY: not needed — 'login_page: LoginPage' is typed, the fixture always returns LoginPage.
     Python's type system + pytest-bdd fixture chaining eliminate defensive instanceof checks.

  4. expect() vs assert:
     TS: expect(await this.pageObj.isLoggedIn()).toBeTruthy()
     PY: assert await login_page.is_logged_in()
     pytest uses plain Python assert statements. On failure, pytest rewrites them to show
     the actual vs expected values in the error output — same quality DX as Jest/Vitest.

  5. toMatch(/regex/) vs re.search():
     TS: expect(error?.toLowerCase()).toMatch(/invalid|not match/)
     PY: assert re.search(r"invalid|not match", error.lower())
     re.search() returns a Match object (truthy) on success, None (falsy) on failure.
     The /g flag is implicit in Python — re.search always scans the full string.
"""

import json
import re
from pathlib import Path

from playwright.async_api import Page
from pytest_bdd import given, scenarios, then, when

from tests.pages.login_page import LoginPage

# Bind all scenarios in login.feature to this test module.
# Background steps (navigate to registration page, fill form, see success message)
# are defined in registration_steps.py and resolved from the global step registry
# because pytest collects both files before running any tests.
scenarios("../features/login.feature")

DATA_PATH = Path(__file__).parent.parent / "support" / "data.json"


@given("I navigate to the login page", target_fixture="login_page")
async def navigate_to_login_page(page: Page) -> LoginPage:
    """
    KEY DIFFERENCE — target_fixture:
    TS: this.pageObj = new LoginPage(this.page)  — mutates World state
    PY: return LoginPage(page)                   — fixture return value becomes 'login_page'

    target_fixture="login_page" tells pytest-bdd: the returned value is a fixture
    named 'login_page'. Subsequent @when/@then steps can declare 'login_page: LoginPage'
    as a parameter and pytest injects the value automatically.
    """
    login_page = LoginPage(page)
    await login_page.goto()
    return login_page


@when("I fill in the login form with valid stored credentials")
async def fill_login_valid(login_page: LoginPage) -> None:
    """
    KEY DIFFERENCE — file I/O:
    TS: JSON.parse(fs.readFileSync(dataPath, 'utf-8'))  — synchronous Node fs module
    PY: json.loads(DATA_PATH.read_text())               — pathlib + standard json module
    Both are synchronous reads; no async needed for local file I/O.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"data.json not found at {DATA_PATH}. Run: task generate-data")
    data = json.loads(DATA_PATH.read_text())
    # Support both 'userName' and 'username' keys — same compatibility as TS version
    username = data.get("userName") or data.get("username")
    password = data.get("password")
    if not username or not password:
        raise ValueError("Stored credentials missing 'userName' or 'password' key")
    await login_page.login(username, password)


@when("I fill in the login form with invalid credentials")
async def fill_login_invalid(login_page: LoginPage) -> None:
    await login_page.login("invalidUser", "invalidPass")


@then("I should see my profile page")
async def see_profile_page(page: Page, login_page: LoginPage) -> None:
    """
    KEY DIFFERENCE — screenshot path:
    TS: await this.page.screenshot({ path: 'reports/login-profile-fail.png', fullPage: true })
    PY: await page.screenshot(path=str(reports_dir / "login-profile-fail.png"), full_page=True)
    Python uses keyword argument 'full_page' (snake_case). The path must be a str, not Path.
    pathlib handles cross-platform path separators automatically.
    """
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    try:
        await page.wait_for_selector("#userName-value", timeout=5000)
    except Exception as exc:
        await page.screenshot(path=str(reports_dir / "login-profile-fail.png"), full_page=True)
        raise AssertionError(
            "Profile page not visible after login. Screenshot saved to reports/login-profile-fail.png"
        ) from exc
    assert await login_page.is_logged_in()


@then("I should see a login error message")
async def see_login_error(login_page: LoginPage) -> None:
    """
    KEY DIFFERENCE — regex matching:
    TS: expect(error?.toLowerCase()).toMatch(/invalid|not match/)
    PY: assert re.search(r"invalid|not match", error.lower())

    re.search() returns a Match object (truthy) if pattern found anywhere in the string,
    None (falsy) if not found — equivalent to Jest's .toMatch() with a regex.
    The TS optional chaining (?.) is replaced by the earlier None assertion.
    """
    error = await login_page.get_error_message()
    assert error is not None, "Expected a login error message, got None"
    assert re.search(r"invalid|not match", error.lower()), f"Unexpected error text: '{error}'"
