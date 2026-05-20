"""
Page Object for demoqa.com/login — async version.
BDD branch equivalent: tests/pages/login_page.py (sync_api)

KEY DIFFERENCE — sync vs async POM:
  BDD branch:    def goto(self) → self.page.goto(url)
  Native branch: async def goto(self) → await self.page.goto(url)

Every method that calls Playwright must be async def and awaited by the caller.
The class itself is identical in structure; only the execution model changes.
"""

from playwright.async_api import Page


class LoginPage:
    LOGIN_URL = "https://demoqa.com/login"
    USERNAME_INPUT = "#userName"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login"
    PROFILE_INDICATOR = "#userName-value"
    ERROR_MESSAGE = "#name"

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        await self.page.goto(self.LOGIN_URL)

    async def login(self, username: str, password: str) -> None:
        await self.page.fill(self.USERNAME_INPUT, username)
        await self.page.fill(self.PASSWORD_INPUT, password)
        await self.page.click(self.LOGIN_BUTTON)

    async def is_logged_in(self) -> bool:
        try:
            await self.page.wait_for_selector(self.PROFILE_INDICATOR, timeout=5000)
            return True
        except Exception:
            return False

    async def get_error_message(self) -> str | None:
        """
        KEY DIFFERENCE — try/except replacing TS try/catch:
        TS: try { return await page.locator("#name").textContent() } catch { return null }
        PY: except Exception: return None
        """
        try:
            return await self.page.locator(self.ERROR_MESSAGE).text_content(timeout=5000)
        except Exception:
            return None
