"""
Page Object for demoqa.com/sortable — sync version for pytest-playwright branch.
"""

import random

from playwright.sync_api import Locator, Page


class SortablePage:
    GRID_TAB = "#demo-tab-grid"
    GRID_ITEMS = ".create-grid .list-group-item"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto("/sortable")
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
        items = self.get_grid_items()
        count = items.count()
        for i in range(count - 1, 0, -1):
            j = random.randint(0, i)
            if i != j:
                items.nth(i).drag_to(items.nth(j))

    def get_grid_order(self) -> list[str]:
        items = self.get_grid_items()
        return [items.nth(i).inner_text() for i in range(items.count())]
