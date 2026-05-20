# KEY DIFFERENCE — API testing without a browser:
#
# Cucumber.js: uses this.apiRequestContext (an APIRequestContext stored on the World object)
#   The World class initialises it in the Before hook when the @api tag is detected.
#   The context is shared across steps via 'this'.
#
# pytest-bdd: uses an api_request_context fixture defined in conftest.py
#   The fixture is injected into step functions by name — no 'this' object needed.
#   pytest detects that the step needs an API context from its parameter signature.
#
# KEY DIFFERENCE — response.status:
#   TypeScript: response.status()  — a METHOD call (returns number)
#   Python:     response.status    — a PROPERTY (no parentheses)
#   This is the most common silent bug when porting Playwright API tests from TS to Python.
#   The code compiles/runs with parentheses in Python but returns a bound method object,
#   which is always truthy — assertions like "assert response.status() == 200" never fail!

@api
Feature: DemoQA Bookstore API

  Scenario: Retrieve all books
    When I request all books from the API
    Then the response should have status 200
    And the response should contain a list of books

  Scenario: Generate a user token
    Given I have valid user credentials
    When I request a token from the API
    Then the response should have status 200
    And the response should contain a token

  Scenario: Call an authenticated API method
    Given I have a valid user token
    When I request my user account details
    Then the response should have status 200
    And the response should contain my user information
