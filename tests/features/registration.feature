# KEY DIFFERENCE — Tag filtering syntax:
#
# Cucumber.js: --tags "not @api"  (CLI flag, tag string includes the @ symbol)
# pytest-bdd:  -m "not api"      (pytest marker, no @ symbol)
#
# In pytest-bdd, Gherkin tags map to pytest markers via the @pytest.mark.<tag> mechanism.
# The @ui tag here becomes pytest.mark.ui, allowing: pytest -m ui  or  pytest -m "not api"
#
# IMPORTANT: pytest markers must be declared in pyproject.toml under [tool.pytest.ini_options]
# markers to avoid "PytestUnknownMarkWarning". Cucumber.js has no equivalent requirement.

@ui
Feature: User Registration
  As a new user
  I want to register on the DemoQA website
  So that I can log in and use the application

  Scenario: Successful registration with valid data
    Given I navigate to the registration page
    When I fill in the registration form with valid data
    Then I should see a success message

  Scenario: Registration fails with invalid password
    Given I navigate to the registration page
    When I fill in the registration form with an invalid password
    Then I should see a validation error message
