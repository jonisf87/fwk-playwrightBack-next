"""
Page Object for demoqa.com/automation-practice-form.
TypeScript equivalent: tests/pages/PracticeFormPage.ts

KEY DIFFERENCES — PracticeFormPage:
  1. page.evaluate() takes a STRING in Python, not a function reference:
     TS: await this.page.evaluate((() => { document.getElementById('fixedban')... }) as () => void)
         → passes a JavaScript arrow function as a value (TypeScript allows this natively)

     PY: await self.page.evaluate("() => { document.getElementById('fixedban')... }")
         → passes the JavaScript as a plain string literal
         The Python Playwright runtime serialises it and evaluates it in the browser context.

     INTERVIEW TRAP: the most common mistake when porting from TS to Python is writing
     'await page.evaluate(lambda: ...)' — this does NOT work. Must be a string of JS.

  2. f-strings replace template literals:
     TS: `label[for="${id}"]`   (backtick template literal)
     PY: f'label[for="{id}"]'  (f-string, curly braces for interpolation)
     Identical result — different syntax.

  3. for...of with array literal → for...in with list literal:
     TS: for (const id of ['hobbies-checkbox-1', 'hobbies-checkbox-2', 'hobbies-checkbox-3'])
     PY: for id in ["hobbies-checkbox-1", "hobbies-checkbox-2", "hobbies-checkbox-3"]:
     Square brackets create a list in Python (not an array — lists are dynamic and mutable).

  4. setInputFiles vs set_input_files:
     TS: await this.page.setInputFiles('#uploadPicture', filePath)
     PY: await self.page.set_input_files("#uploadPicture", file_path)
     One of many camelCase → snake_case conversions in the Python Playwright API.

  5. keyboard.press vs keyboard.press (identical):
     TS: await this.page.keyboard.press('Enter')
     PY: await self.page.keyboard.press("Enter")
     This one is identical — the Playwright team kept keyboard API names consistent.
"""

from playwright.async_api import Locator, Page


class PracticeFormPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    async def hide_overlays(self) -> None:
        """
        Remove ad banners and modals that intercept pointer events.

        KEY DIFFERENCE: page.evaluate() receives a JavaScript STRING in Python.
        TypeScript passes a function reference/arrow function — Python cannot do this.
        The JS string is sent to the browser and evaluated there; same end result.

        Note the triple-quoted string for multiline JS — Python equivalent of TS template literals
        for multiline code blocks.
        """
        await self.page.evaluate(
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

    async def goto(self) -> None:
        await self.page.goto("https://demoqa.com/automation-practice-form")

    async def fill_first_name(self, value: str) -> None:
        await self.page.fill("#firstName", value)

    async def fill_last_name(self, value: str) -> None:
        await self.page.fill("#lastName", value)

    async def fill_email(self, value: str) -> None:
        await self.page.fill("#userEmail", value)

    async def select_gender(self) -> None:
        # Click "Other" gender radio — label targeting is more reliable than input targeting
        await self.page.locator('label[for="gender-radio-3"]').click()

    async def fill_mobile(self, value: str) -> None:
        await self.page.fill("#userNumber", value)

    async def set_date_of_birth(self, date: str) -> None:
        # Format expected: "dd mmm yyyy" e.g. "15 Jan 1990"
        await self.page.click("#dateOfBirthInput")
        await self.page.fill("#dateOfBirthInput", date)
        await self.page.press("#dateOfBirthInput", "Enter")

    async def fill_subjects(self, subjects: list[str]) -> None:
        """
        KEY DIFFERENCE: Type hint for list parameter.
        TS: subjects: string[]    — TypeScript array syntax
        PY: subjects: list[str]   — Python generic syntax (PEP 585, Python 3.9+)
        Older Python style: List[str] from typing — still valid but deprecated.
        """
        for subject in subjects:
            await self.page.fill("#subjectsInput", subject)
            await self.page.keyboard.press("Enter")

    async def select_hobbies(self) -> None:
        await self.hide_overlays()
        # KEY DIFFERENCE: f-string replaces template literal — see module docstring, point 2
        for hobby_id in ["hobbies-checkbox-1", "hobbies-checkbox-2", "hobbies-checkbox-3"]:
            await self.page.locator(f'label[for="{hobby_id}"]').click()

    async def upload_picture(self, file_path: str) -> None:
        # KEY DIFFERENCE: set_input_files vs setInputFiles — see module docstring, point 4
        await self.page.set_input_files("#uploadPicture", file_path)

    async def fill_current_address(self, value: str) -> None:
        await self.page.fill("#currentAddress", value)

    async def select_state_and_city(self, state: str, city: str) -> None:
        # React-select dropdowns: click to open, then click the option
        await self.page.click("#state")
        await self.page.locator(f'div[id^="react-select-3-option"]:has-text("{state}")').click()
        await self.page.click("#city")
        await self.page.locator(f'div[id^="react-select-4-option"]:has-text("{city}")').click()

    async def submit(self) -> None:
        await self.page.click("#submit")

    async def get_confirmation_modal(self) -> Locator:
        # KEY DIFFERENCE: return type is Locator (imported from playwright.async_api)
        # TS: return type is inferred as Locator — no explicit annotation needed
        # PY: mypy strict mode requires explicit return type on all functions
        return self.page.locator(".modal-content")

    async def get_email_error(self) -> Locator:
        # ':invalid' is a CSS pseudo-class — works the same in both TS and PY
        return self.page.locator("#userEmail:invalid")
