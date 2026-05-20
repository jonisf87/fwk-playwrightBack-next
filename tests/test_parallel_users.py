"""
Multi-user interaction tests using pytest-playwright (sync).

KEY DIFFERENCE vs feature/native-playwright:
  That branch runs both users CONCURRENTLY with asyncio.gather():
    result_form, result_grid = await asyncio.gather(
        _user1_form_task(browser),
        _user2_grid_task(browser),
    )
  This branch runs them SEQUENTIALLY. Both approaches create isolated
  BrowserContext objects per user (independent cookies, storage, network).

  The concurrent version requires async_api + asyncio_mode = "auto".
  This branch uses pytest-playwright's sync fixtures and gains native
  Playwright reports (screenshot + trace on failure) in exchange.

ISOLATED CONTEXTS PATTERN:
  Each user task calls browser.new_context() independently. This is the same
  pattern as TypeScript's browser.newContext(). The contexts share the same
  browser process but have completely separate session state.

  TS: const context = await this.browser.newContext()
  PY:       context =       browser.new_context()      (sync, no await)
"""

import re
from pathlib import Path

import pytest
from faker import Faker
from playwright.sync_api import Browser

from tests.pages.practice_form_page import PracticeFormPage
from tests.pages.sortable_page import SortablePage

fake = Faker()
SAMPLE_IMAGE = Path(__file__).parent / "fixtures" / "test-image.png"


def _user1_form_task(browser: Browser) -> bool:
    """User 1: fill and submit the automation practice form in an isolated context."""
    context = browser.new_context()
    page = context.new_page()
    try:
        form = PracticeFormPage(page)
        form.goto()
        form.hide_overlays()
        form.fill_first_name(fake.first_name())
        form.fill_last_name(fake.last_name())
        form.fill_email(fake.email())
        form.select_gender()
        form.fill_mobile(fake.numerify("##########"))
        form.set_date_of_birth("10 Oct 1990")
        form.fill_subjects(["Maths", "English"])
        form.select_hobbies()
        form.upload_picture(str(SAMPLE_IMAGE))
        form.fill_current_address(fake.street_address())
        form.select_state_and_city("NCR", "Delhi")
        form.submit()

        found = False
        try:
            modal = page.locator(".modal-content")
            modal.wait_for(state="attached", timeout=7000)
            for _ in range(10):
                text = modal.text_content()
                if text and re.search(r"thanks for submitting the form", text, re.IGNORECASE):
                    found = True
                    break
                page.wait_for_timeout(300)
        except Exception:
            found = False
        return found
    finally:
        context.close()


def _user2_grid_task(browser: Browser) -> bool:
    """User 2: navigate to sortable, switch to grid tab, shuffle items."""
    context = browser.new_context()
    page = context.new_page()
    try:
        sortable = SortablePage(page)
        sortable.goto()
        sortable.go_to_grid_tab()
        before = sortable.get_grid_order()
        sortable.shuffle_grid_items()
        after = sortable.get_grid_order()
        return before != after
    finally:
        context.close()


def _user1_invalid_email_task(browser: Browser) -> bool:
    context = browser.new_context()
    page = context.new_page()
    try:
        form = PracticeFormPage(page)
        form.goto()
        form.fill_first_name(fake.first_name())
        form.fill_last_name(fake.last_name())
        form.fill_email("invalid-email")
        is_valid = page.eval_on_selector("#userEmail", "(el) => el.validity.valid")
        return not is_valid
    finally:
        context.close()


@pytest.mark.ui
def test_two_users_sequential(browser: Browser) -> None:
    """
    Two users interact with different pages using isolated BrowserContext objects.
    Runs sequentially (user 1 completes, then user 2 starts).

    For true concurrent execution see feature/native-playwright which uses:
      asyncio.gather(_user1_form_task(browser), _user2_grid_task(browser))
    """
    form_submitted = _user1_form_task(browser)
    grid_changed = _user2_grid_task(browser)
    assert form_submitted, "User 1 did not see form submission confirmation"
    assert grid_changed, "User 2 did not see grid items reordered after shuffle"


@pytest.mark.ui
def test_invalid_email_validation(browser: Browser) -> None:
    email_error_shown = _user1_invalid_email_task(browser)
    assert email_error_shown, "HTML5 email validation did not fire for 'invalid-email'"
