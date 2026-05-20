"""
Page Object for demoqa.com/register.
TypeScript equivalent: tests/pages/RegistrationPage.ts

KEY DIFFERENCES — RegistrationPage:
  1. Shorthand constructor in TypeScript ('private' auto-assigns) vs Python's explicit __init__:
     TS: constructor(private page: Page) {}   — 'page' is declared AND assigned in one line
     PY: def __init__(self, page: Page) -> None: self.page = page  — always explicit

  2. CAPTCHA frame detection — most important difference in this class:
     TS: const captchaFrame = frames.find(f => f.url().includes('google.com/recaptcha'))
         → Array.find() returns the first match or undefined

     PY: captcha_frame = next((f for f in self.page.frames if "google.com/recaptcha" in f.url), None)
         → next() on a generator expression returns the first match or None (the default)

     The pattern 'next((x for x in iterable if condition), default)' is the idiomatic Python
     replacement for JavaScript's Array.find(). It short-circuits on first match.

     Also note: TS uses f.url() (method call) — PY uses f.url (property, no parentheses).

  3. Locator waitFor vs wait_for:
     TS: await this.page.locator(sel).waitFor({ state: 'visible', timeout: 10000 })
     PY: await self.page.locator(sel).wait_for(state="visible", timeout=10000)
     Identical semantics, snake_case in Python.

  4. Return types for getters:
     TS: async getSuccessMessage() — implicit return type (inferred as Promise<string | null>)
     PY: async def get_success_message(self) -> str | None  — explicit annotation required by mypy
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

    async def goto(self) -> None:
        await self.page.goto("https://demoqa.com/register")

    async def fill_first_name(self, first_name: str) -> None:
        await self.page.locator(self.FIRST_NAME_INPUT).wait_for(state="visible", timeout=10000)
        await self.page.fill(self.FIRST_NAME_INPUT, first_name)

    async def fill_last_name(self, last_name: str) -> None:
        await self.page.locator(self.LAST_NAME_INPUT).wait_for(state="visible", timeout=10000)
        await self.page.fill(self.LAST_NAME_INPUT, last_name)

    async def fill_username(self, username: str) -> None:
        await self.page.locator(self.USERNAME_INPUT).wait_for(state="visible", timeout=10000)
        await self.page.fill(self.USERNAME_INPUT, username)

    async def fill_password(self, password: str) -> None:
        await self.page.locator(self.PASSWORD_INPUT).wait_for(state="visible", timeout=10000)
        await self.page.fill(self.PASSWORD_INPUT, password)

    async def click_captcha_checkbox(self) -> None:
        """
        Attempt to click the reCAPTCHA iframe checkbox if present.

        KEY DIFFERENCE: CAPTCHA frame detection — see module docstring, point 2.
        TS: const captchaFrame = frames.find(f => f.url().includes('google.com/recaptcha'))
        PY: next((f for f in self.page.frames if "google.com/recaptcha" in f.url), None)

        'f.url' in Python is a property (no parentheses).
        'f.url()' in TypeScript is a method call.
        This is one of the most common bugs when porting Playwright from TS to Python.
        """
        # KEY DIFFERENCE: self.page.frames is a list property in Python.
        # TS: this.page.frames() — method call returning array
        # PY: self.page.frames  — property returning list (no parentheses)
        captcha_frame = next(
            (f for f in self.page.frames if "google.com/recaptcha" in f.url),
            None,
        )
        if captcha_frame:
            try:
                await captcha_frame.click("#recaptcha-anchor", timeout=5000)
            except Exception:  # noqa: BLE001
                pass  # ignore if CAPTCHA is not interactable — same as TS catch {}

    async def click_register(self) -> None:
        await self.page.click(self.REGISTER_BUTTON)

    async def get_success_message(self) -> str | None:
        # KEY DIFFERENCE: text_content() vs textContent()
        # Both return the text of the element or None if the element has no text.
        return await self.page.locator(self.SUCCESS_MESSAGE).text_content()

    async def get_error_message(self) -> str | None:
        return await self.page.locator(self.ERROR_MESSAGE).text_content()
