"""
Page Object for demoqa.com/register.
TypeScript equivalent: tests/pages/RegistrationPage.ts

KEY DIFFERENCES — RegistrationPage:
  1. SYNC API — no async/await in this branch.
     TS: await this.page.goto(...)
     PY: self.page.goto(...)    (sync, blocks until complete)

  2. CAPTCHA frame detection:
     TS: const captchaFrame = frames.find(f => f.url().includes('google.com/recaptcha'))
         → Array.find() with f.url() as METHOD CALL

     PY: next((f for f in self.page.frames if "google.com/recaptcha" in f.url), None)
         → next() on generator expression; f.url is a PROPERTY (no parentheses)

     Using f.url() in Python would return a bound method object (always truthy).
     This is one of the most common bugs when porting Playwright from TS to Python.

  3. Locator waitFor vs wait_for:
     TS: await this.page.locator(sel).waitFor({ state: 'visible', timeout: 10000 })
     PY: self.page.locator(sel).wait_for(state="visible", timeout=10000)
     Identical semantics, snake_case in Python.
"""

from playwright.sync_api import Page


class RegistrationPage:
    FIRST_NAME_INPUT = 'input#firstname[placeholder="First Name"]'
    LAST_NAME_INPUT = 'input#lastname[placeholder="Last Name"]'
    USERNAME_INPUT = 'input#userName[placeholder="UserName"]'
    PASSWORD_INPUT = 'input#password[placeholder="Password"]'
    REGISTER_BUTTON = "#register"
    SUCCESS_MESSAGE = ".text-success"
    ERROR_MESSAGE = "#name"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto("https://demoqa.com/register")

    def fill_first_name(self, first_name: str) -> None:
        self.page.locator(self.FIRST_NAME_INPUT).wait_for(state="visible", timeout=10000)
        self.page.fill(self.FIRST_NAME_INPUT, first_name)

    def fill_last_name(self, last_name: str) -> None:
        self.page.locator(self.LAST_NAME_INPUT).wait_for(state="visible", timeout=10000)
        self.page.fill(self.LAST_NAME_INPUT, last_name)

    def fill_username(self, username: str) -> None:
        self.page.locator(self.USERNAME_INPUT).wait_for(state="visible", timeout=10000)
        self.page.fill(self.USERNAME_INPUT, username)

    def fill_password(self, password: str) -> None:
        self.page.locator(self.PASSWORD_INPUT).wait_for(state="visible", timeout=10000)
        self.page.fill(self.PASSWORD_INPUT, password)

    def click_captcha_checkbox(self) -> None:
        """
        Attempt to click the reCAPTCHA iframe checkbox if present.

        KEY DIFFERENCE: f.url is a PROPERTY in Python (no parentheses).
        TS: f.url()  → Python: f.url
        Writing f.url() in Python returns a bound method object (always truthy).
        """
        captcha_frame = next(
            (f for f in self.page.frames if "google.com/recaptcha" in f.url),
            None,
        )
        if captcha_frame:
            try:
                captcha_frame.click("#recaptcha-anchor", timeout=5000)
            except Exception:  # noqa: BLE001
                pass

    def click_register(self) -> None:
        self.page.click(self.REGISTER_BUTTON)

    def get_success_message(self) -> str | None:
        return self.page.locator(self.SUCCESS_MESSAGE).text_content()

    def get_error_message(self) -> str | None:
        """
        KEY DIFFERENCE — try/except wraps the locator call:
        TS: try { return await page.locator("#name").textContent({ timeout: 15000 }) } catch { return null }
        PY: use try/except so missing element returns None instead of raising TimeoutError.
        """
        try:
            return self.page.locator(self.ERROR_MESSAGE).text_content(timeout=15000)
        except Exception:
            return None
