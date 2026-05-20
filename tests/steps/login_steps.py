"""
BDD step definitions for login.feature.
TypeScript equivalent: tests/steps/Login.steps.ts

KEY DIFFERENCES — Step definitions:

  1. SYNC API — this branch uses playwright.sync_api (no async/await).
     pytest-bdd calls step functions via _execute_step_function which is synchronous.
     Async step functions return unawaited coroutines — their bodies never execute.
     Using sync_api means all Playwright calls block until complete, matching
     pytest-bdd's execution model exactly.

     The native branch (feature/native-playwright) uses async_api with asyncio.gather()
     for true concurrent user simulation — there, test functions are async def and
     pytest-asyncio manages the event loop correctly.

  2. 'this' context vs fixture injection:
     TS: Given('...', async function (this: CustomWorld) { this.pageObj = new LoginPage(...) })
     PY: @given("...", target_fixture="login_page")
         def _(page: Page) -> LoginPage: return LoginPage(page)
     The return value of a @given with target_fixture becomes a named fixture available
     to all subsequent steps in the same scenario.

  3. isinstance() guard removed:
     TS: if (this.pageObj instanceof LoginPage) { ... } else { throw Error(...) }
     PY: not needed — 'login_page: LoginPage' is typed, the fixture always returns LoginPage.

  4. expect() vs assert:
     TS: expect(await this.pageObj.isLoggedIn()).toBeTruthy()
     PY: assert login_page.is_logged_in()
     No await needed — sync API.

  5. toMatch(/regex/) vs re.search():
     TS: expect(error?.toLowerCase()).toMatch(/invalid|not match/)
     PY: assert re.search(r"invalid|not match", error.lower())
"""

import json
import re
from pathlib import Path

from playwright.sync_api import Page
from pytest_bdd import given, scenarios, then, when

from tests.pages.login_page import LoginPage

scenarios("../features/login.feature")

DATA_PATH = Path(__file__).parent.parent / "support" / "data.json"


@given("I navigate to the login page", target_fixture="login_page")
def navigate_to_login_page(page: Page) -> LoginPage:
    """
    KEY DIFFERENCE — target_fixture:
    TS: this.pageObj = new LoginPage(this.page)  — mutates World state
    PY: return LoginPage(page)                   — fixture return value becomes 'login_page'
    Subsequent @when/@then steps declare 'login_page: LoginPage' and pytest injects it.
    """
    login_page = LoginPage(page)
    login_page.goto()
    return login_page


@when("I fill in the login form with valid stored credentials")
def fill_login_valid(login_page: LoginPage) -> None:
    """
    KEY DIFFERENCE — file I/O:
    TS: JSON.parse(fs.readFileSync(dataPath, 'utf-8'))
    PY: json.loads(DATA_PATH.read_text())
    Both synchronous reads; pathlib replaces Node's fs module.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"data.json not found at {DATA_PATH}. Run: task generate-data")
    data = json.loads(DATA_PATH.read_text())
    username = data.get("userName") or data.get("username")
    password = data.get("password")
    if not username or not password:
        raise ValueError("Stored credentials missing 'userName' or 'password' key")
    login_page.login(username, password)


@when("I fill in the login form with invalid credentials")
def fill_login_invalid(login_page: LoginPage) -> None:
    login_page.login("invalidUser", "invalidPass")


@then("I should see my profile page")
def see_profile_page(page: Page, login_page: LoginPage) -> None:
    """
    KEY DIFFERENCE — screenshot path:
    TS: await this.page.screenshot({ path: '...', fullPage: true })
    PY: page.screenshot(path=str(reports_dir / "..."), full_page=True)
    snake_case keyword arg; path must be str, not Path.
    """
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    try:
        page.wait_for_selector("#userName-value", timeout=5000)
    except Exception as exc:
        page.screenshot(path=str(reports_dir / "login-profile-fail.png"), full_page=True)
        raise AssertionError(
            "Profile page not visible after login. Screenshot saved to reports/login-profile-fail.png"
        ) from exc
    assert login_page.is_logged_in()


@then("I should see a login error message")
def see_login_error(login_page: LoginPage) -> None:
    """
    KEY DIFFERENCE — regex matching:
    TS: expect(error?.toLowerCase()).toMatch(/invalid|not match/)
    PY: assert re.search(r"invalid|not match", error.lower())
    re.search() returns a Match object (truthy) on success, None (falsy) on failure.
    """
    error = login_page.get_error_message()
    assert error is not None, "Expected a login error message, got None"
    assert re.search(r"invalid|not match", error.lower()), f"Unexpected error text: '{error}'"
