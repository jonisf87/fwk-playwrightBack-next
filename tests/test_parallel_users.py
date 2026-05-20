"""
Native Playwright parallel users test — the key differentiator from the BDD branch.
BDD branch equivalent: tests/features/parallel_users.feature + tests/steps/parallel_users_steps.py

═══════════════════════════════════════════════════════════════════════════════
THE MOST IMPORTANT ARCHITECTURAL DIFFERENCE IN THIS FILE
═══════════════════════════════════════════════════════════════════════════════

BDD branch — SEQUENTIAL execution:
  @when("user 1 fills and submits the form")  ← runs to completion
  def user_1_submits_form(browser): ...        ← then returns

  @when("user 2 shuffles the sortable grid")  ← only starts AFTER user 1 finishes
  def user_2_shuffles_grid(browser): ...

  Reason: pytest-bdd calls step functions synchronously via _execute_step_function.
  Even if we marked them async def, the coroutines would never be awaited.
  Sequential = user 1 completes all actions, then user 2 starts.

Native branch — TRUE CONCURRENT execution:
  result_form, result_grid = await asyncio.gather(
      user_1_task(browser),   ← both START at the same time
      user_2_task(browser),   ← on the SAME asyncio event loop
  )

  asyncio.gather() schedules both coroutines on the event loop simultaneously.
  While user_1 is waiting for a network response, the event loop can advance
  user_2. This is cooperative concurrency (single thread, multiple coroutines)
  — the same model as JavaScript's Promise.all().

KEY DIFFERENCE — asyncio.gather() vs Promise.all():
  TS: const [r1, r2] = await Promise.all([task1(), task2()])
  PY: r1, r2 = await asyncio.gather(task1(), task2())

  Both:
  - Start all tasks at the same time
  - Await all of them before continuing
  - Return results in the same order as the input
  - Are cooperative (yield at I/O boundaries), not preemptive (no OS threads)

KEY DIFFERENCE — isolated browser contexts per user:
  Each user gets their own BrowserContext (independent cookies, localStorage,
  network state). The BROWSER instance is shared — only the context is new.
  TS: const context = await this.browser.newContext()
  PY: context = await browser.new_context()   (async, no 'await this.browser')
"""

import asyncio
import re
from pathlib import Path

import pytest
from faker import Faker
from playwright.async_api import Browser

from tests.pages.practice_form_page import PracticeFormPage
from tests.pages.sortable_page import SortablePage

fake = Faker()
SAMPLE_IMAGE = Path(__file__).parent / "fixtures" / "test-image.png"


async def _user1_form_task(browser: Browser) -> bool:
    """
    User 1: fill and submit the automation practice form.
    Returns True if the confirmation modal appears.

    Runs concurrently with _user2_grid_task via asyncio.gather().
    Each await is a potential yield point where the event loop can
    advance the other coroutine.
    """
    context = await browser.new_context()
    page = await context.new_page()
    try:
        form = PracticeFormPage(page)
        await form.goto()
        await form.hide_overlays()
        await form.fill_first_name(fake.first_name())
        await form.fill_last_name(fake.last_name())
        await form.fill_email(fake.email())
        await form.select_gender()
        await form.fill_mobile(fake.numerify("##########"))
        await form.set_date_of_birth("10 Oct 1990")
        await form.fill_subjects(["Maths", "English"])
        await form.select_hobbies()
        await form.upload_picture(str(SAMPLE_IMAGE))
        await form.fill_current_address(fake.street_address())
        await form.select_state_and_city("NCR", "Delhi")
        await form.submit()

        found = False
        try:
            modal = page.locator(".modal-content")
            await modal.wait_for(state="attached", timeout=7000)
            for _ in range(10):
                text = await modal.text_content()
                if text and re.search(r"thanks for submitting the form", text, re.IGNORECASE):
                    found = True
                    break
                await page.wait_for_timeout(300)
        except Exception:
            found = False
        return found
    finally:
        await context.close()


async def _user2_grid_task(browser: Browser) -> bool:
    """
    User 2: navigate to sortable, switch to grid tab, shuffle items.
    Returns True if the grid order changed after shuffling.

    KEY DIFFERENCE — await on every Playwright call (vs sync in BDD):
      BDD:    before = sortable.get_grid_order()  (sync)
      Native: before = await sortable.get_grid_order()
    """
    context = await browser.new_context()
    page = await context.new_page()
    try:
        sortable = SortablePage(page)
        await sortable.goto()
        await sortable.go_to_grid_tab()

        before = await sortable.get_grid_order()
        await sortable.shuffle_grid_items()
        after = await sortable.get_grid_order()

        # KEY DIFFERENCE — direct list comparison:
        # TS: before.join(',') !== after.join(',')
        # PY: before != after   (Python list __eq__ compares element-by-element)
        return before != after
    finally:
        await context.close()


async def _user1_invalid_email_task(browser: Browser) -> bool:
    """User 1: fill form with invalid email, check HTML5 validation fires."""
    context = await browser.new_context()
    page = await context.new_page()
    try:
        form = PracticeFormPage(page)
        await form.goto()
        await form.fill_first_name(fake.first_name())
        await form.fill_last_name(fake.last_name())
        await form.fill_email("invalid-email")

        # KEY DIFFERENCE — eval_on_selector replaces TS page.$eval:
        # TS: await page.$eval('#userEmail', (el: HTMLInputElement) => el.validity.valid)
        # PY: await page.eval_on_selector('#userEmail', '(el) => el.validity.valid')
        #     The JS function must be a STRING — Python functions are not JS.
        is_valid = await page.eval_on_selector("#userEmail", "(el) => el.validity.valid")
        return not is_valid
    finally:
        await context.close()


@pytest.mark.ui
async def test_two_users_parallel(browser: Browser) -> None:
    """
    THE KEY TEST — demonstrates asyncio.gather() for true concurrent execution.

    TS equivalent: await Promise.all([task1(this.browser), task2(this.browser)])
    PY equivalent: await asyncio.gather(task1(browser), task2(browser))

    Both coroutines start simultaneously. While user_1 waits for a page load,
    the event loop advances user_2 — I/O-bound tasks overlap in wall-clock time.
    """
    form_submitted, grid_changed = await asyncio.gather(
        _user1_form_task(browser),
        _user2_grid_task(browser),
    )
    assert form_submitted, "User 1 did not see form submission confirmation"
    assert grid_changed, "User 2 did not see grid items reordered after shuffle"


@pytest.mark.ui
async def test_invalid_email_validation(browser: Browser) -> None:
    email_error_shown = await _user1_invalid_email_task(browser)
    assert email_error_shown, "HTML5 email validation did not fire for 'invalid-email'"
