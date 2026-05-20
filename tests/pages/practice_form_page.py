"""
Page Object for demoqa.com/automation-practice-form — sync version.

KEY DIFFERENCE vs feature/native-playwright:
  That branch uses async def + await throughout.
  This branch is sync: plain def, no await, pytest-playwright's page fixture.
"""

from playwright.sync_api import Page


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

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto(
            "/automation-practice-form",
            wait_until="domcontentloaded",
        )

    def hide_overlays(self) -> None:
        self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, .modal, .modal-backdrop, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )

    def fill_first_name(self, v: str) -> None:
        self.page.fill(self.FIRST_NAME, v)

    def fill_last_name(self, v: str) -> None:
        self.page.fill(self.LAST_NAME, v)

    def fill_email(self, v: str) -> None:
        self.page.fill(self.EMAIL, v)

    def select_gender(self) -> None:
        self.page.locator(self.GENDER_MALE).click(force=True)

    def fill_mobile(self, v: str) -> None:
        self.page.fill(self.MOBILE, v)

    def set_date_of_birth(self, date_str: str) -> None:
        self.page.click(self.DATE_OF_BIRTH)
        self.page.fill(self.DATE_OF_BIRTH, date_str)
        self.page.keyboard.press("Escape")

    def fill_subjects(self, subjects: list[str]) -> None:
        for subject in subjects:
            self.page.fill(self.SUBJECTS_INPUT, subject)
            self.page.keyboard.press("Enter")

    def select_hobbies(self) -> None:
        self.page.locator(self.HOBBY_SPORTS).click(force=True)

    def upload_picture(self, file_path: str) -> None:
        self.page.set_input_files(self.UPLOAD_PICTURE, file_path)

    def fill_current_address(self, v: str) -> None:
        self.page.fill(self.CURRENT_ADDRESS, v)

    def select_state_and_city(self, state: str, city: str) -> None:
        self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, .modal, .modal-backdrop, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )
        self.page.locator(self.STATE_SELECT).scroll_into_view_if_needed()
        self.page.locator(self.STATE_SELECT).click(force=True)
        self.page.get_by_text(state, exact=True).click()
        self.page.locator(self.CITY_SELECT).click(force=True)
        self.page.get_by_text(city, exact=True).click()

    def submit(self) -> None:
        self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )
        self.page.locator(self.SUBMIT_BUTTON).scroll_into_view_if_needed()
        self.page.locator(self.SUBMIT_BUTTON).click(force=True)
