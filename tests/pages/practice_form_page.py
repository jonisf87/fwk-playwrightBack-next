"""
Page Object for demoqa.com/automation-practice-form.
TypeScript equivalent: tests/pages/PracticeFormPage.ts

KEY DIFFERENCES — PracticeFormPage:
  1. SYNC API — no async/await in this branch.
     TS: await this.page.fill("#firstName", value)
     PY: self.page.fill("#firstName", value)    (sync, no await)

  2. page.evaluate() takes a STRING in Python, not a function reference:
     TS: await this.page.evaluate((() => { document.getElementById('fixedban')... }) as () => void)
         → passes a JavaScript arrow function as a TypeScript value

     PY: self.page.evaluate("() => { document.getElementById('fixedban')... }")
         → passes the JavaScript as a plain string literal

     INTERVIEW TRAP: 'page.evaluate(lambda: ...)' does NOT work in Python.
     Must always be a string of JavaScript code.

  3. f-strings replace template literals:
     TS: `label[for="${id}"]`   (backtick template literal)
     PY: f'label[for="{id}"]'  (f-string, curly braces for interpolation)

  4. for...of with array literal → for...in with list literal:
     TS: for (const id of ['hobbies-checkbox-1', ...])
     PY: for id in ["hobbies-checkbox-1", ...]:

  5. set_input_files vs setInputFiles:
     TS: await this.page.setInputFiles('#uploadPicture', filePath)
     PY: self.page.set_input_files("#uploadPicture", file_path)

  6. list[str] vs string[]:
     TS: subjects: string[]    — TypeScript array syntax
     PY: subjects: list[str]   — Python generic syntax (PEP 585, Python 3.9+)
"""

from playwright.sync_api import Locator, Page


class PracticeFormPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def hide_overlays(self) -> None:
        """
        Remove ad banners and modals that intercept pointer events.

        KEY DIFFERENCE: page.evaluate() receives a JavaScript STRING.
        TypeScript passes a function reference; Python requires a string literal.
        """
        self.page.evaluate(
            """() => {
                const fixedban = document.getElementById('fixedban');
                if (fixedban) fixedban.style.display = 'none';
                const adPlus = document.getElementById('adplus-anchor');
                if (adPlus) adPlus.style.display = 'none';
                document.querySelectorAll('.modal, .modal-backdrop, [role="dialog"]')
                    .forEach(el => { el.style.display = 'none'; });
                document.querySelectorAll('iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )

    def goto(self) -> None:
        self.page.goto("https://demoqa.com/automation-practice-form")

    def fill_first_name(self, value: str) -> None:
        self.page.fill("#firstName", value)

    def fill_last_name(self, value: str) -> None:
        self.page.fill("#lastName", value)

    def fill_email(self, value: str) -> None:
        self.page.fill("#userEmail", value)

    def select_gender(self) -> None:
        self.page.locator('label[for="gender-radio-3"]').click()

    def fill_mobile(self, value: str) -> None:
        self.page.fill("#userNumber", value)

    def set_date_of_birth(self, date: str) -> None:
        self.page.click("#dateOfBirthInput")
        self.page.fill("#dateOfBirthInput", date)
        self.page.press("#dateOfBirthInput", "Enter")

    def fill_subjects(self, subjects: list[str]) -> None:
        for subject in subjects:
            self.page.fill("#subjectsInput", subject)
            self.page.keyboard.press("Enter")

    def select_hobbies(self) -> None:
        self.hide_overlays()
        for hobby_id in ["hobbies-checkbox-1", "hobbies-checkbox-2", "hobbies-checkbox-3"]:
            self.page.locator(f'label[for="{hobby_id}"]').click()

    def upload_picture(self, file_path: str) -> None:
        self.page.set_input_files("#uploadPicture", file_path)

    def fill_current_address(self, value: str) -> None:
        self.page.fill("#currentAddress", value)

    def select_state_and_city(self, state: str, city: str) -> None:
        self.page.click("#state")
        self.page.locator(f'div[id^="react-select-3-option"]:has-text("{state}")').click()
        self.page.click("#city")
        self.page.locator(f'div[id^="react-select-4-option"]:has-text("{city}")').click()

    def submit(self) -> None:
        self.page.click("#submit")

    def get_confirmation_modal(self) -> Locator:
        return self.page.locator(".modal-content")

    def get_email_error(self) -> Locator:
        return self.page.locator("#userEmail:invalid")
