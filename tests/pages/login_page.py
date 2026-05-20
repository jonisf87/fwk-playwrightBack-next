"""
Page Object for demoqa.com/login.
TypeScript equivalent: tests/pages/LoginPage.ts

KEY DIFFERENCES — LoginPage:
  1. No 'export' keyword. Python modules export everything by default; you control visibility
     with __all__ or leading underscores. 'import LoginPage from ...' doesn't exist in Python.

  2. Class-level selector constants use UPPER_SNAKE_CASE (PEP 8 convention for constants).
     TS: readonly usernameInput = '#userName'  (instance property set once at construction)
     PY: USERNAME_INPUT = '#userName'          (class-level constant, shared across instances)
     Both are effectively immutable in practice, but Python has no 'readonly' keyword.

  3. Constructor: 'private page: Page' auto-assigns in TypeScript.
     Python requires explicit self.page = page in __init__.
     TS: constructor(private page: Page) {}
     PY: def __init__(self, page: Page) -> None: self.page = page

  4. Return type syntax:
     TS: async isLoggedIn(): Promise<boolean>
     PY: async def is_logged_in(self) -> bool:
     The 'Promise<T>' wrapper disappears — Python's asyncio handles the event loop implicitly.

  5. Nullable return type:
     TS: Promise<string | null>
     PY: str | None   (PEP 604, Python 3.10+)
     Older style: Optional[str] from typing — still valid but more verbose.

  6. try/except vs try/catch:
     TS: try { ... } catch { ... }   — catch with no variable is valid TS 4.0+
     PY: try: ... except Exception:  — Python always names the exception clause
     'except Exception' catches all non-system-exiting exceptions, equivalent to bare 'catch {}'.
"""

from playwright.async_api import Page


class LoginPage:
    # Selectors as class constants — see KEY DIFFERENCE 2 above
    USERNAME_INPUT = "#userName"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login"
    LOGOUT_BUTTON = "#submit"

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        await self.page.goto("https://demoqa.com/login")

    async def login(self, username: str, password: str) -> None:
        await self.page.fill(self.USERNAME_INPUT, username)
        await self.page.fill(self.PASSWORD_INPUT, password)
        await self.page.click(self.LOGIN_BUTTON)

    async def is_logged_in(self) -> bool:
        # KEY DIFFERENCE: snake_case method names throughout the Playwright Python API.
        # TS: this.page.isVisible(selector)
        # PY: self.page.is_visible(selector)
        return await self.page.is_visible(self.LOGOUT_BUTTON)

    async def get_error_message(self) -> str | None:
        """
        Try multiple selectors in order, return first non-empty text found.
        Strategy identical to TypeScript — resilience against demoqa.com DOM variability.

        KEY DIFFERENCE: for...of loop → for...in loop (Python has only 'for...in')
        TS: for (const selector of selectors) { ... }
        PY: for selector in selectors: ...
        Both iterate over the list sequentially — no functional difference.
        """
        selectors = [
            "#name",
            ".mb-1",
            ".text-danger",
            ".alert-danger",
            ".error-message",
        ]
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, state="visible", timeout=3000)
                text = await self.page.text_content(selector)
                if text and text.strip():
                    return text.strip()
            except Exception:  # noqa: BLE001 — broad catch mirrors TS bare 'catch {}'
                continue
        return None
