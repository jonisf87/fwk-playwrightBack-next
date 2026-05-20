"""
Page Object for demoqa.com/sortable.
TypeScript equivalent: tests/pages/SortablePage.ts

KEY DIFFERENCES — SortablePage:
  1. Fisher-Yates shuffle — random number generation:
     TS: Math.floor(Math.random() * (i + 1))
         → generates a random float in [0, 1), multiplies by (i+1), floors to integer
         → result range: 0 to i inclusive

     PY: random.randint(0, i)
         → generates a random integer in [0, i] inclusive (BOTH ends included)
         → this is a critical difference: Python's randint is inclusive on BOTH ends
         → equivalent range to the TS formula, but much more readable

     INTERVIEW TRAP: Python's range(n) and random.randrange(n) exclude the upper bound,
     but random.randint(a, b) INCLUDES both a and b. Always clarify when asked.

  2. Reverse iteration:
     TS: for (let i = count - 1; i > 0; i--)
         → classic C-style for loop with decrement

     PY: for i in range(count - 1, 0, -1):
         → range(start, stop, step) — stop is EXCLUSIVE, so 0 is not included
         → equivalent to i going from count-1 down to 1 (stopping before 0)
         → the step=-1 makes it count down

  3. Drag and drop — identical API:
     TS: await items.nth(i).dragTo(items.nth(j))
     PY: await items.nth(i).drag_to(items.nth(j))
     Only the snake_case difference.

  4. innerText vs inner_text:
     TS: await items.nth(i).innerText()
     PY: await items.nth(i).inner_text()
     Classic camelCase → snake_case conversion.

  5. Locator type annotation:
     TS: async getGridItems() — return type inferred as Locator
     PY: async def get_grid_items(self) -> Locator  — must be explicit for mypy strict
"""

import random

from playwright.async_api import Locator, Page


class SortablePage:
    GRID_TAB = "a#demo-tab-grid"
    GRID_ITEMS = ".create-grid .list-group-item"

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        await self.page.goto("https://demoqa.com/sortable")

    async def go_to_grid_tab(self) -> None:
        await self.page.click(self.GRID_TAB)

    async def get_grid_items(self) -> Locator:
        return self.page.locator(self.GRID_ITEMS)

    async def shuffle_grid_items(self) -> None:
        """
        Fisher-Yates in-place shuffle using Playwright drag-and-drop.

        KEY DIFFERENCE: random number generation — see module docstring, point 1.
        TS: Math.floor(Math.random() * (i + 1))  →  integer in [0, i]
        PY: random.randint(0, i)                  →  integer in [0, i] (both inclusive)
        """
        items = await self.get_grid_items()
        count = await items.count()

        # KEY DIFFERENCE: range(start, stop, step) — see module docstring, point 2
        # TS: for (let i = count - 1; i > 0; i--)
        # PY: for i in range(count - 1, 0, -1):   — stop=0 is excluded, so i goes down to 1
        for i in range(count - 1, 0, -1):
            j = random.randint(0, i)  # inclusive on both ends — equiv to Math.floor(Math.random()*(i+1))
            if i != j:
                await items.nth(i).drag_to(items.nth(j))

    async def get_grid_order(self) -> list[str]:
        """
        Return current grid item labels as a list.

        KEY DIFFERENCE: list[str] vs string[]:
        TS: const order: string[] = []   — TypeScript array type syntax
        PY: order: list[str] = []        — Python generic list (PEP 585, Python 3.9+)

        KEY DIFFERENCE: inner_text() vs innerText()
        TS: await items.nth(i).innerText()
        PY: await items.nth(i).inner_text()
        """
        items = await self.get_grid_items()
        count = await items.count()
        order: list[str] = []

        # KEY DIFFERENCE: range(n) is exclusive, so range(count) = 0, 1, ..., count-1
        # TS: for (let i = 0; i < count; i++)
        # PY: for i in range(count):
        for i in range(count):
            order.append(await items.nth(i).inner_text())
        return order
