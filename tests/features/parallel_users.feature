# KEY DIFFERENCE — File naming convention:
#
# TypeScript original: parallelUsers.feature  (camelCase — JavaScript/Node convention)
# Python equivalent:   parallel_users.feature (snake_case — PEP 8 Python convention)
#
# Gherkin content is identical. The rename is purely a Python style convention.
# pytest-bdd resolves the path via scenarios("../features/parallel_users.feature")
# in the corresponding step definition file.
#
# KEY DIFFERENCE — Parallel execution model:
#
# This scenario tests two browser contexts running concurrently.
# TypeScript: uses Promise.all([task1(), task2()]) — native to Node.js event loop
# Python:     uses asyncio.gather(task1(), task2()) — asyncio cooperative multitasking
#
# Both approaches are single-threaded concurrency (cooperative, not preemptive).
# True multi-threading is possible in Python with threading.Thread, but asyncio is
# the idiomatic choice for I/O-bound tasks like browser automation.

@ui
Feature: Parallel user simulation for Practice Form and Sortable Grid

  Scenario: Two users interact with different pages in parallel
    When user 1 fills and submits the automation practice form with valid data
    And user 2 shuffles the sortable grid items
    Then user 1 should see the form submission confirmation
    And user 2 should see the grid items reordered

  Scenario: User 1 submits the form with an invalid email
    When user 1 fills the automation practice form with an invalid email
    Then user 1 should see an email validation error
