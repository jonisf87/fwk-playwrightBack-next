"""
Page Object for demoqa.com/register — sync version for pytest-playwright branch.
"""

from playwright.sync_api import Page


class RegistrationPage:
    FIRST_NAME_INPUT = 'input#firstname[placeholder="First Name"]'
    LAST_NAME_INPUT = 'input#lastname[placeholder="Last Name"]'
    USERNAME_INPUT = 'input#userName[placeholder="UserName"]'
    PASSWORD_INPUT = 'input#password[placeholder="Password"]'
    REGISTER_BUTTON = "#register"
    ERROR_MESSAGE = "#name"

    def __init__(self, page: Page) -> None:
        self.page = page
        self._registration_message: str | None = None
        self._registration_error: str | None = None

    def goto(self) -> None:
        self.page.goto("/register")

    def fill_first_name(self, v: str) -> None:
        self.page.locator(self.FIRST_NAME_INPUT).wait_for(state="visible", timeout=10000)
        self.page.fill(self.FIRST_NAME_INPUT, v)

    def fill_last_name(self, v: str) -> None:
        self.page.fill(self.LAST_NAME_INPUT, v)

    def fill_username(self, v: str) -> None:
        self.page.fill(self.USERNAME_INPUT, v)

    def fill_password(self, v: str) -> None:
        self.page.fill(self.PASSWORD_INPUT, v)

    def click_captcha_checkbox(self) -> None:
        captcha_frame = next((f for f in self.page.frames if "google.com/recaptcha" in f.url), None)
        if captcha_frame:
            try:
                captcha_frame.click("#recaptcha-anchor", timeout=5000)
            except Exception:
                pass

    def click_register(self) -> None:
        self.page.click(self.REGISTER_BUTTON)

    def get_error_message(self) -> str | None:
        try:
            return self.page.locator(self.ERROR_MESSAGE).text_content(timeout=15000)
        except Exception:
            return None
