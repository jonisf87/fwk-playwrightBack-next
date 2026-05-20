"""
BDD step definitions for parallel_users.feature.
TypeScript equivalent: tests/steps/ParallelUsers.steps.ts

KEY DIFFERENCES — Parallel users:

  1. SYNC API — no async/await in this branch.
     TS: const context = await this.browser.newContext()
     PY: context = browser.new_context()    (sync, blocks until complete)

  2. Sequential execution in BDD branch vs true concurrency in native branch:
     This BDD branch runs user 1 and user 2 SEQUENTIALLY (separate @When steps).
     Each step creates its own isolated browser context, does its work, closes it.

     The native branch (feature/native-playwright) uses TRUE concurrency:
     TS: await Promise.all([task1(), task2()])
     PY: await asyncio.gather(task1(), task2())

     Both are cooperative (single-threaded) concurrency on an event loop.
     The BDD branch can't use asyncio.gather() because step functions are sync.

  3. page.$eval() vs eval_on_selector():
     TS: await page.$eval('#userEmail', (el: HTMLInputElement) => el.validity.valid)
     PY: page.eval_on_selector('#userEmail', '(el) => el.validity.valid')
     page.$eval() in TS passes a JS function as a TypeScript value — in Python it must be a string.

  4. inner_html() / text_content() on missing elements:
     TS: form.page.locator('.modal-content').innerHTML().catch(() => '')
     PY: try: modal.inner_html() \n    except: modal_html = ''

  5. wait_for_timeout vs waitForTimeout:
     TS: await page.waitForTimeout(300)
     PY: page.wait_for_timeout(300)    (sync, snake_case)
"""

import re
from pathlib import Path

from faker import Faker
from playwright.sync_api import Browser
from pytest_bdd import scenarios, then, when

from tests.conftest import ScenarioContext
from tests.pages.practice_form_page import PracticeFormPage
from tests.pages.sortable_page import SortablePage

scenarios("../features/parallel_users.feature")

fake = Faker()
SAMPLE_IMAGE = Path(__file__).parent.parent / "fixtures" / "test-image.png"


@when("user 1 fills and submits the automation practice form with valid data")
def user_1_submits_form(browser: Browser, ctx: ScenarioContext) -> None:
    """
    Creates an isolated browser context for user 1.
    TS: const context = await this.browser.newContext()
    PY: context = browser.new_context()    (sync)
    """
    context = browser.new_context()
    page = context.new_page()

    form = PracticeFormPage(page)
    form.goto()
    form.hide_overlays()
    form.fill_first_name(fake.first_name())
    form.fill_last_name(fake.last_name())
    form.fill_email(fake.email())
    form.select_gender()
    # KEY DIFFERENCE: fake.numerify() replaces faker.string.numeric()
    # TS: faker.string.numeric('##########')  →  PY: fake.numerify('##########')
    form.fill_mobile(fake.numerify("##########"))
    form.set_date_of_birth("10 Oct 1990")
    form.fill_subjects(["Maths", "English"])
    form.select_hobbies()
    form.upload_picture(str(SAMPLE_IMAGE))
    # KEY DIFFERENCE: fake.street_address() replaces faker.location.streetAddress()
    form.fill_current_address(fake.street_address())
    form.select_state_and_city("NCR", "Delhi")
    form.submit()

    found_confirmation = False
    try:
        modal = page.locator(".modal-content")
        modal.wait_for(state="attached", timeout=7000)
        for _ in range(10):
            text = modal.text_content()
            if text and re.search(r"thanks for submitting the form", text, re.IGNORECASE):
                found_confirmation = True
                break
            page.wait_for_timeout(300)
    except Exception:
        found_confirmation = False
        try:
            modal_html = page.locator(".modal-content").inner_html()
        except Exception:
            modal_html = ""
        print(f"DEBUG: No confirmation modal. Modal HTML: {modal_html}")

    ctx.form_confirmation = found_confirmation
    context.close()


@when("user 2 shuffles the sortable grid items")
def user_2_shuffles_grid(browser: Browser, ctx: ScenarioContext) -> None:
    """
    Creates an isolated browser context for user 2.
    """
    context = browser.new_context()
    page = context.new_page()

    sortable = SortablePage(page)
    sortable.goto()
    sortable.go_to_grid_tab()

    before = sortable.get_grid_order()
    sortable.shuffle_grid_items()
    after = sortable.get_grid_order()

    # KEY DIFFERENCE: direct list comparison
    # TS: before.join(',') !== after.join(',')
    # PY: before != after
    ctx.grid_order_changed = before != after
    context.close()


@when("user 1 fills the automation practice form with an invalid email")
def user_1_invalid_email(browser: Browser, ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — HTML5 validation check:
    TS: await page.$eval('#userEmail', (el: HTMLInputElement) => el.validity.valid)
        page.$eval passes a TypeScript function — in Python it must be a JS string.
    PY: page.eval_on_selector('#userEmail', '(el) => el.validity.valid')
    """
    context = browser.new_context()
    page = context.new_page()

    form = PracticeFormPage(page)
    form.goto()
    form.fill_first_name(fake.first_name())
    form.fill_last_name(fake.last_name())
    form.fill_email("invalid-email")

    is_valid = page.eval_on_selector("#userEmail", "(el) => el.validity.valid")

    if not is_valid:
        try:
            form.submit()
            page.wait_for_timeout(500)
            email_error_locator = form.get_email_error()
            ctx.email_error = email_error_locator.is_visible()
        except Exception:
            ctx.email_error = True
    else:
        ctx.email_error = False

    context.close()


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
