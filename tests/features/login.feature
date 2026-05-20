# KEY DIFFERENCE — How feature files are connected to steps:
#
# Cucumber.js (TypeScript):
#   Feature files are discovered via a glob in the CLI command:
#     cucumber-js tests/features/**/*.feature --require tests/steps/*.ts
#   Steps are auto-discovered globally — any matching step in any loaded file is used.
#   No explicit binding between a .feature file and its step definitions.
#
# pytest-bdd (Python):
#   Feature files must be EXPLICITLY bound in a test module using one of two approaches:
#     1. scenarios("../features/login.feature")  — registers all scenarios in the file
#     2. @scenario("../features/login.feature", "Scenario name")  — registers one scenario
#   This gives pytest-bdd precise control over which test module owns which scenarios.
#   It also means feature files appear as proper pytest test items with IDs you can filter.
#
# The Gherkin syntax itself is 100% identical between Cucumber.js and pytest-bdd.
# Tags (@ui, @api) work the same way — pytest uses -m "not api" instead of --tags "not @api".

@ui
Feature: Login
  As a registered user
  I want to log in to the application
  So that I can access my profile

  Background:
    Given I navigate to the registration page
    When I fill in the registration form with valid data
    Then I should see a success message

  Scenario: Successful login with valid credentials
    Given I navigate to the login page
    When I fill in the login form with valid stored credentials
    Then I should see my profile page

  Scenario: Login fails with invalid credentials
    Given I navigate to the login page
    When I fill in the login form with invalid credentials
    Then I should see a login error message
