"""
Page Object for demoqa.com/automation-practice-form — async version.
BDD branch equivalent: tests/pages/practice_form_page.py (sync_api)

KEY DIFFERENCE — page.evaluate() takes a JS string, not a Python function:
  TS: await page.evaluate(() => { document.querySelector(...).remove() })
      The lambda IS a TypeScript/JavaScript function passed as a value.
  PY: await page.evaluate("() => { document.querySelector(...).remove() }")
      Must be a STRING containing a JS function — Python functions are not JS.

KEY DIFFERENCE — async POM:
  Every method is async def; every Playwright call is awaited.
"""

from playwright.async_api import Page


class PracticeFormPage:
    FIRST_NAME = "#firstName"
    LAST_NAME = "#lastName"
    EMAIL = "#userEmail"
    GENDER_MALE = "label[for='gender-radio-1']"
    MOBILE = "#userNumber"
    DATE_OF_BIRTH = "#dateOfBirthInput"
    SUBJECTS_INPUT = "#subjectsInput"
    HOBBY_SPORTS = "label[for='hobbies-checkbox-1']"
    UPLOAD_PICTURE = "#uploadPicture"
    CURRENT_ADDRESS = "#currentAddress"
    STATE_SELECT = "#state"
    CITY_SELECT = "#city"
    SUBMIT_BUTTON = "#submit"
    EMAIL_ERROR = "#userEmail.field-error, #userEmail:invalid"

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        # wait_until="domcontentloaded" instead of the default "load" so we don't
        # wait for every ad/analytics script — much faster in CI, especially Firefox.
        await self.page.goto(
            "https://demoqa.com/automation-practice-form",
            wait_until="domcontentloaded",
        )

    async def hide_overlays(self) -> None:
        """
        KEY DIFFERENCE — page.evaluate() takes a JS string:
        TS: await page.evaluate(() => { ... })  — inline arrow function
        PY: await page.evaluate("() => { ... }")  — JS as a string literal
        """
        await self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, .modal, .modal-backdrop, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )

    async def fill_first_name(self, name: str) -> None:
        await self.page.fill(self.FIRST_NAME, name)

    async def fill_last_name(self, name: str) -> None:
        await self.page.fill(self.LAST_NAME, name)

    async def fill_email(self, email: str) -> None:
        await self.page.fill(self.EMAIL, email)

    async def select_gender(self) -> None:
        await self.page.locator(self.GENDER_MALE).click(force=True)

    async def fill_mobile(self, mobile: str) -> None:
        await self.page.fill(self.MOBILE, mobile)

    async def set_date_of_birth(self, date_str: str) -> None:
        await self.page.click(self.DATE_OF_BIRTH)
        await self.page.fill(self.DATE_OF_BIRTH, date_str)
        await self.page.keyboard.press("Escape")

    async def fill_subjects(self, subjects: list[str]) -> None:
        for subject in subjects:
            await self.page.fill(self.SUBJECTS_INPUT, subject)
            await self.page.keyboard.press("Enter")

    async def select_hobbies(self) -> None:
        await self.page.locator(self.HOBBY_SPORTS).click(force=True)

    async def upload_picture(self, file_path: str) -> None:
        await self.page.set_input_files(self.UPLOAD_PICTURE, file_path)

    async def fill_current_address(self, address: str) -> None:
        await self.page.fill(self.CURRENT_ADDRESS, address)

    async def select_state_and_city(self, state: str, city: str) -> None:
        # Re-hide overlays: new ad iframes may have loaded since hide_overlays() ran.
        await self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, .modal, .modal-backdrop, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )
        await self.page.locator(self.STATE_SELECT).scroll_into_view_if_needed()
        await self.page.locator(self.STATE_SELECT).click(force=True)
        await self.page.get_by_text(state, exact=True).click()
        await self.page.locator(self.CITY_SELECT).click(force=True)
        await self.page.get_by_text(city, exact=True).click()

    async def submit(self) -> None:
        await self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )
        await self.page.locator(self.SUBMIT_BUTTON).scroll_into_view_if_needed()
        await self.page.locator(self.SUBMIT_BUTTON).click(force=True)

    async def get_email_error(self) -> bool:
        """
        KEY DIFFERENCE — eval_on_selector vs page.evaluate with querySelector:
        TS: await page.$eval('#userEmail', (el: HTMLInputElement) => el.validity.valid)
        PY: await page.evaluate('(el) => el.validity.valid',
                await page.query_selector('#userEmail'))
        Or more directly: await page.eval_on_selector('#userEmail', '(el) => el.validity.valid')
        """
        return not await self.page.eval_on_selector(self.EMAIL, "(el) => el.validity.valid")
