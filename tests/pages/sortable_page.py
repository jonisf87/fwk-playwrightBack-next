"""
Page Object for demoqa.com/sortable.
TypeScript equivalent: tests/pages/SortablePage.ts

KEY DIFFERENCES — SortablePage:
  1. SYNC API — no async/await in this branch.
     TS: count = await items.count()
     PY: count = items.count()    (sync, blocks until complete)

  2. Fisher-Yates shuffle — random number generation:
     TS: Math.floor(Math.random() * (i + 1))   → integer in [0, i]
     PY: random.randint(0, i)                   → integer in [0, i] (BOTH ends inclusive)

     INTERVIEW TRAP: Python's range(n) and random.randrange(n) exclude the upper bound,
     but random.randint(a, b) INCLUDES both a and b.

  3. Reverse iteration:
     TS: for (let i = count - 1; i > 0; i--)
     PY: for i in range(count - 1, 0, -1):
         range(start, stop, step) — stop is EXCLUSIVE (0 not included), step=-1 counts down.

  4. drag_to vs dragTo:
     TS: await items.nth(i).dragTo(items.nth(j))
     PY: items.nth(i).drag_to(items.nth(j))    (snake_case, no await)

  5. inner_text vs innerText:
     TS: await items.nth(i).innerText()
     PY: items.nth(i).inner_text()
"""

import random

from playwright.sync_api import Locator, Page


class SortablePage:
    GRID_TAB = "#demo-tab-grid"  # demoqa changed <a> to <button> — selector without tag is stable
    GRID_ITEMS = ".create-grid .list-group-item"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto("https://demoqa.com/sortable")
        # Remove ad overlays that intercept pointer events (same pattern as PracticeFormPage)
        self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, .modal, .modal-backdrop, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )

    def go_to_grid_tab(self) -> None:
        tab = self.page.locator(self.GRID_TAB)
        tab.scroll_into_view_if_needed()
        tab.click()

    def get_grid_items(self) -> Locator:
        return self.page.locator(self.GRID_ITEMS)

    def shuffle_grid_items(self) -> None:
        """Fisher-Yates in-place shuffle using Playwright drag-and-drop."""
        items = self.get_grid_items()
        count = items.count()
        # KEY DIFFERENCE: range(start, stop, step) — stop=0 is excluded, so i goes down to 1
        for i in range(count - 1, 0, -1):
            j = random.randint(0, i)  # inclusive both ends — equiv to Math.floor(Math.random()*(i+1))
            if i != j:
                items.nth(i).drag_to(items.nth(j))

    def get_grid_order(self) -> list[str]:
        """Return current grid item labels as a list."""
        items = self.get_grid_items()
        count = items.count()
        order: list[str] = []
        for i in range(count):
            order.append(items.nth(i).inner_text())
        return order
