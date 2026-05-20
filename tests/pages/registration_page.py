"""
Page Object for demoqa.com/register — async version.
BDD branch equivalent: tests/pages/registration_page.py (sync_api)

KEY DIFFERENCE — async POM:
  BDD branch uses playwright.sync_api.Page; all methods are def + no await.
  Native branch uses playwright.async_api.Page; all methods are async def + await.
  The POM structure is identical — only the execution model differs.
"""

from playwright.async_api import Page


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
        self._registration_message: str | None = None
        self._registration_error: str | None = None

    async def goto(self) -> None:
        await self.page.goto("https://demoqa.com/register")

    async def fill_first_name(self, first_name: str) -> None:
        await self.page.locator(self.FIRST_NAME_INPUT).wait_for(state="visible", timeout=10000)
        await self.page.fill(self.FIRST_NAME_INPUT, first_name)

    async def fill_last_name(self, last_name: str) -> None:
        await self.page.fill(self.LAST_NAME_INPUT, last_name)

    async def fill_username(self, username: str) -> None:
        await self.page.fill(self.USERNAME_INPUT, username)

    async def fill_password(self, password: str) -> None:
        await self.page.fill(self.PASSWORD_INPUT, password)

    async def click_captcha_checkbox(self) -> None:
        """
        KEY DIFFERENCE: f.url is a PROPERTY in Python (no parentheses).
        TS: f.url()  → PY: f.url
        Writing f.url() returns a bound method object (always truthy).
        """
        captcha_frame = next(
            (f for f in self.page.frames if "google.com/recaptcha" in f.url),
            None,
        )
        if captcha_frame:
            try:
                await captcha_frame.click("#recaptcha-anchor", timeout=5000)
            except Exception:
                pass

    async def click_register(self) -> None:
        await self.page.click(self.REGISTER_BUTTON)

    async def get_error_message(self) -> str | None:
        try:
            return await self.page.locator(self.ERROR_MESSAGE).text_content(timeout=15000)
        except Exception:
            return None
