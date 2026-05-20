"""
Page Object for demoqa.com/sortable — async version.
BDD branch equivalent: tests/pages/sortable_page.py (sync_api)

KEY DIFFERENCES vs BDD branch:
  1. async def + await on every Playwright call.
  2. items.count() → await items.count()
  3. items.nth(i).drag_to(items.nth(j)) → await items.nth(i).drag_to(items.nth(j))
  4. items.nth(i).inner_text() → await items.nth(i).inner_text()

Fisher-Yates shuffle and random.randint() are identical — Python stdlib, no async.

UI NOTE: demoqa changed the Grid tab from <a> to <button>.
  Selector 'a#demo-tab-grid' no longer matches — use '#demo-tab-grid' (tag-agnostic).
"""

import random

from playwright.async_api import Locator, Page


class SortablePage:
    GRID_TAB = "#demo-tab-grid"  # demoqa changed <a> to <button> — omit tag prefix
    GRID_ITEMS = ".create-grid .list-group-item"

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        await self.page.goto("https://demoqa.com/sortable")
        await self.page.evaluate(
            """() => {
                document.querySelectorAll('#fixedban, #adplus-anchor, .modal, .modal-backdrop, iframe')
                    .forEach(el => { el.style.display = 'none'; });
            }"""
        )

    async def go_to_grid_tab(self) -> None:
        tab = self.page.locator(self.GRID_TAB)
        await tab.scroll_into_view_if_needed()
        await tab.click()

    def get_grid_items(self) -> Locator:
        return self.page.locator(self.GRID_ITEMS)

    async def shuffle_grid_items(self) -> None:
        """
        Fisher-Yates shuffle using async Playwright drag_to.

        KEY DIFFERENCE — async drag_to:
          BDD:    items.nth(i).drag_to(items.nth(j))    (sync, no await)
          Native: await items.nth(i).drag_to(items.nth(j))  (async)

        KEY DIFFERENCE — await items.count():
          BDD:    count = items.count()
          Native: count = await items.count()
        """
        items = self.get_grid_items()
        count = await items.count()
        for i in range(count - 1, 0, -1):
            j = random.randint(0, i)
            if i != j:
                await items.nth(i).drag_to(items.nth(j))

    async def get_grid_order(self) -> list[str]:
        items = self.get_grid_items()
        count = await items.count()
        order: list[str] = []
        for i in range(count):
            order.append(await items.nth(i).inner_text())
        return order
