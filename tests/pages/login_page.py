"""
Page Object for demoqa.com/login.
TypeScript equivalent: tests/pages/LoginPage.ts

KEY DIFFERENCES — LoginPage:
  1. No 'export' keyword. Python modules export everything by default.

  2. Class-level selector constants use UPPER_SNAKE_CASE (PEP 8 convention for constants).
     TS: readonly usernameInput = '#userName'  (instance property set once at construction)
     PY: USERNAME_INPUT = '#userName'          (class-level constant, shared across instances)

  3. Constructor: 'private page: Page' auto-assigns in TypeScript.
     Python requires explicit self.page = page in __init__.

  4. SYNC API — this branch uses playwright.sync_api, NOT playwright.async_api.
     TS: await this.page.goto("...")     — async, requires await
     PY: self.page.goto("...")           — sync, blocks until complete (no await)

     pytest-bdd calls step functions synchronously via _execute_step_function.
     It does not await coroutines from async step functions — the coroutine body
     never executes. Using sync_api matches pytest-bdd's execution model perfectly.
     The native branch (feature/native-playwright) uses async_api + asyncio.gather().

  5. Nullable return type:
     TS: Promise<string | null>
     PY: str | None   (PEP 604, Python 3.10+)

  6. try/except vs try/catch:
     TS: try { ... } catch { ... }
     PY: try: ... except Exception:
"""

from playwright.sync_api import Page


class LoginPage:
    USERNAME_INPUT = "#userName"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login"
    LOGOUT_BUTTON = "#submit"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto("https://demoqa.com/login")

    def login(self, username: str, password: str) -> None:
        self.page.fill(self.USERNAME_INPUT, username)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.LOGIN_BUTTON)

    def is_logged_in(self) -> bool:
        # KEY DIFFERENCE: snake_case throughout Playwright Python API.
        # TS: this.page.isVisible(selector)
        # PY: self.page.is_visible(selector)
        return self.page.is_visible(self.LOGOUT_BUTTON)

    def get_error_message(self) -> str | None:
        """
        Try multiple selectors, return first non-empty text found.

        KEY DIFFERENCE: for...of → for...in (Python has only 'for...in').
        TS: for (const selector of selectors) { ... }
        PY: for selector in selectors: ...
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
                self.page.wait_for_selector(selector, state="visible", timeout=3000)
                text = self.page.text_content(selector)
                if text and text.strip():
                    return text.strip()
            except Exception:  # noqa: BLE001
                continue
        return None
