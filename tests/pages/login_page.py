"""
Page Object for demoqa.com/login — sync version for pytest-playwright branch.

KEY DIFFERENCE vs feature/native-playwright:
  That branch: async def goto(self) / await self.page.goto(url)
  This branch:      def goto(self) /       self.page.goto(url)

pytest-playwright provides a sync Page fixture. Every method is a plain def.
"""

from playwright.sync_api import Page


class LoginPage:
    LOGIN_URL = "/login"
    USERNAME_INPUT = "#userName"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login"
    PROFILE_INDICATOR = "#userName-value"
    ERROR_MESSAGE = "#name"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto(self.LOGIN_URL)

    def login(self, username: str, password: str) -> None:
        self.page.fill(self.USERNAME_INPUT, username)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.LOGIN_BUTTON)

    def is_logged_in(self) -> bool:
        try:
            self.page.wait_for_selector(self.PROFILE_INDICATOR, timeout=5000)
            return True
        except Exception:
            return False

    def get_error_message(self) -> str | None:
        try:
            return self.page.locator(self.ERROR_MESSAGE).text_content(timeout=5000)
        except Exception:
            return None
