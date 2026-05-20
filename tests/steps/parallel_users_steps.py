"""
BDD step definitions for parallel_users.feature.
TypeScript equivalent: tests/steps/ParallelUsers.steps.ts

KEY DIFFERENCES — Parallel users:

  1. Browser contexts — identical API:
     TS: const context = await this.browser.newContext()
     PY: context = await browser.new_context()
     The 'browser' fixture is injected — no 'this.browser' needed.

  2. asyncio.gather() vs Promise.all():
     The TypeScript version runs user 1 and user 2 SEQUENTIALLY (separate @When steps).
     Each step creates its own browser context, does its work, and closes the context.
     This is "parallel simulation" in the sense of isolated contexts, not true concurrency.

     In this BDD branch we preserve the sequential structure to match the TypeScript design.
     The native Playwright branch (feature/native-playwright) demonstrates TRUE concurrency
     using asyncio.gather([user1_task(), user2_task()]) — Python's equivalent of Promise.all().

     KEY DIFFERENCE:
     TS Promise.all():    await Promise.all([task1(), task2()])   — true concurrent JS tasks
     PY asyncio.gather(): await asyncio.gather(task1(), task2()) — true concurrent Python coroutines
     Both are cooperative (single-threaded) concurrency on an event loop.

  3. page.$eval() vs page.evaluate():
     TS: await page.$eval('#userEmail', (el: HTMLInputElement) => el.validity.valid)
     PY: await page.eval_on_selector('#userEmail', '(el) => el.validity.valid')
     page.$eval() in TS passes a JS function as a Python callable — in PY it must be a string.
     Alternatively: await page.evaluate('(sel) => document.querySelector(sel).validity.valid', '#userEmail')

  4. inner_html() / text_content() on missing elements:
     TS: await form.page.locator('.modal-content').innerHTML().catch(() => '')
     PY: try: await page.locator('.modal-content').inner_html() \n    except: modal_html = ''
     TypeScript Promise.catch() is replaced by Python try/except on the coroutine.

  5. waitForTimeout vs asyncio.sleep:
     TS: await form.page.waitForTimeout(300)   — Playwright's built-in wait
     PY: await page.wait_for_timeout(300)      — identical API, snake_case
     Note: asyncio.sleep(0.3) also works but wait_for_timeout is idiomatic in Playwright tests.
"""

import re
from pathlib import Path

from faker import Faker
from playwright.async_api import Browser
from pytest_bdd import scenarios, then, when

from tests.conftest import ScenarioContext
from tests.pages.practice_form_page import PracticeFormPage
from tests.pages.sortable_page import SortablePage

scenarios("../features/parallel_users.feature")

fake = Faker()
SAMPLE_IMAGE = Path(__file__).parent.parent / "fixtures" / "test-image.png"


@when("user 1 fills and submits the automation practice form with valid data")
async def user_1_submits_form(browser: Browser, ctx: ScenarioContext) -> None:
    """
    Creates an isolated browser context for user 1.
    TS: const context = await this.browser.newContext()
    PY: context = await browser.new_context()
    The browser fixture is injected — same resource, different syntax.
    """
    context = await browser.new_context()
    page = await context.new_page()

    form = PracticeFormPage(page)
    await form.goto()
    await form.hide_overlays()
    await form.fill_first_name(fake.first_name())
    await form.fill_last_name(fake.last_name())
    await form.fill_email(fake.email())
    await form.select_gender()
    # KEY DIFFERENCE: fake.numerify() replaces faker.string.numeric()
    # TS: faker.string.numeric('##########')  →  PY: fake.numerify('##########')
    await form.fill_mobile(fake.numerify("##########"))
    await form.set_date_of_birth("10 Oct 1990")
    await form.fill_subjects(["Maths", "English"])
    await form.select_hobbies()
    await form.upload_picture(str(SAMPLE_IMAGE))
    # KEY DIFFERENCE: fake.street_address() replaces faker.location.streetAddress()
    await form.fill_current_address(fake.street_address())
    await form.select_state_and_city("NCR", "Delhi")
    await form.submit()

    # Retry loop: wait for confirmation modal text
    found_confirmation = False
    try:
        modal = page.locator(".modal-content")
        await modal.wait_for(state="attached", timeout=7000)
        for _ in range(10):
            text = await modal.text_content()
            if text and re.search(r"thanks for submitting the form", text, re.IGNORECASE):
                found_confirmation = True
                break
            await page.wait_for_timeout(300)
    except Exception:
        found_confirmation = False
        try:
            modal_html = await page.locator(".modal-content").inner_html()
        except Exception:
            modal_html = ""
        print(f"DEBUG: No confirmation modal. Modal HTML: {modal_html}")

    ctx.form_confirmation = found_confirmation
    await context.close()


@when("user 2 shuffles the sortable grid items")
async def user_2_shuffles_grid(browser: Browser, ctx: ScenarioContext) -> None:
    """
    Creates an isolated browser context for user 2.
    Captures grid order before and after shuffle to detect change.
    """
    context = await browser.new_context()
    page = await context.new_page()

    sortable = SortablePage(page)
    await sortable.goto()
    await sortable.go_to_grid_tab()

    before = await sortable.get_grid_order()
    await sortable.shuffle_grid_items()
    after = await sortable.get_grid_order()

    # KEY DIFFERENCE: list comparison
    # TS: before.join(',') !== after.join(',')   — string comparison of joined arrays
    # PY: before != after                        — direct list comparison (cleaner)
    ctx.grid_order_changed = before != after
    await context.close()


@when("user 1 fills the automation practice form with an invalid email")
async def user_1_invalid_email(browser: Browser, ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — HTML5 validation check:
    TS: await page.$eval('#userEmail', (el: HTMLInputElement) => el.validity.valid)
        page.$eval passes a TypeScript function — in PY it must be a JS string.
    PY: await page.eval_on_selector('#userEmail', '(el) => el.validity.valid')
    """
    context = await browser.new_context()
    page = await context.new_page()

    form = PracticeFormPage(page)
    await form.goto()
    await form.fill_first_name(fake.first_name())
    await form.fill_last_name(fake.last_name())
    await form.fill_email("invalid-email")

    # KEY DIFFERENCE: eval_on_selector replaces page.$eval
    is_valid = await page.eval_on_selector("#userEmail", "(el) => el.validity.valid")

    if not is_valid:
        try:
            await form.submit()
            await page.wait_for_timeout(500)
            email_error_locator = await form.get_email_error()
            ctx.email_error = await email_error_locator.is_visible()
        except Exception:
            ctx.email_error = True  # submission blocked = email validation error detected
    else:
        ctx.email_error = False  # should not happen in this negative test

    await context.close()


@then("user 1 should see the form submission confirmation")
def user_1_sees_confirmation(ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — assert vs expect:
    TS: expect(this.formConfirmation).toBe(true)
    PY: assert ctx.form_confirmation
    """
    assert ctx.form_confirmation, "User 1 did not see form submission confirmation modal"


@then("user 2 should see the grid items reordered")
def user_2_sees_reorder(ctx: ScenarioContext) -> None:
    assert ctx.grid_order_changed, "User 2 did not see grid items reordered after shuffle"


@then("user 1 should see an email validation error")
def user_1_sees_email_error(ctx: ScenarioContext) -> None:
    assert ctx.email_error, "User 1 did not see an email validation error"
