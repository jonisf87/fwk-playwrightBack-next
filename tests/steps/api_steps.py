"""
BDD step definitions for api.feature.
TypeScript equivalent: tests/steps/Api.steps.ts

KEY DIFFERENCES — API steps:

  1. CRITICAL — response.status is a PROPERTY, not a method:
     TS: expect(this.apiResponse!.status()).toBe(200)   — status() is a method call
     PY: assert ctx.api_response.status == 200          — status is a property (integer)
     Writing ctx.api_response.status() in Python returns a bound method — always truthy.
     This is the most common silent Playwright bug when porting from TypeScript to Python.

  2. Non-null assertion (!) vs guaranteed fixture:
     TS: this.apiRequestContext!.get(url)  — '!' asserts non-null at compile time
     PY: api_request_context.get(url)      — fixture is guaranteed non-None by conftest.py
     Python has no '!' operator. The fixture lifecycle ensures the context is always valid.

  3. await response.json() is a coroutine:
     TS: const body = await response.json()
     PY: body = await response.json()
     Identical — both are async. Confirmed consistent.

  4. typeof vs isinstance():
     TS: typeof body.token === 'string'
     PY: isinstance(body.get("token"), str)
     Python's isinstance() checks the runtime type of an object.
     'typeof' in TS returns a string name; isinstance() in PY returns a bool directly.

  5. Dict access vs object property access:
     TS: body.token           — object property dot notation
     PY: body.get("token")    — dict .get() with None default (safe access)
     OR: body["token"]        — raises KeyError if missing (use when key must exist)
     Python dicts use [] or .get() — no dot access on plain dicts.

  6. Short-circuit OR for nullable fields:
     TS: regBody.userID || regBody.userId || regBody.id
     PY: reg_body.get("userID") or reg_body.get("userId") or reg_body.get("id")
     Python's 'or' short-circuits just like JavaScript's '||'.

  7. Date.now() vs time.time():
     TS: 'testuser_' + Date.now()    — milliseconds since epoch (integer)
     PY: f"testuser_{int(time.time() * 1000)}"  — same scale (multiply by 1000)
     time.time() returns seconds as float; * 1000 gives milliseconds like Date.now().
"""

import time

from playwright.async_api import APIRequestContext
from pytest_bdd import given, scenarios, then, when

from tests.conftest import ScenarioContext

scenarios("../features/api.feature")

BASE_URL = "https://demoqa.com"


@given("I have valid user credentials")
def have_valid_credentials(ctx: ScenarioContext) -> None:
    """
    Synchronous step — no browser or network needed, just sets data on ctx.

    KEY DIFFERENCE — Date.now() vs time.time():
    TS: userName: 'testuser_' + Date.now()          — ms since epoch
    PY: "userName": f"testuser_{int(time.time() * 1000)}"  — same scale
    """
    ctx.api_user = {
        "userName": f"testuser_{int(time.time() * 1000)}",
        "password": "Password1!",
    }


@when("I request all books from the API")
async def request_all_books(api_request_context: APIRequestContext, ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — api_request_context fixture vs World:
    TS: await this.apiRequestContext!.get(url)   — '!' non-null assertion
    PY: await api_request_context.get(url)       — fixture, always valid (no '!' needed)
    """
    response = await api_request_context.get(f"{BASE_URL}/BookStore/v1/Books")
    ctx.api_response = response
    ctx.api_response_body = await response.json()


@when("I request a token from the API")
async def request_token(api_request_context: APIRequestContext, ctx: ScenarioContext) -> None:
    """Register user then generate auth token."""
    if not ctx.api_user:
        ctx.api_user = {
            "userName": f"testuser_{int(time.time() * 1000)}",
            "password": "Password1!",
        }

    # Register (201 = created, 406 = already exists — both acceptable)
    reg_response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=ctx.api_user,
        headers={"Content-Type": "application/json"},
    )
    reg_body = await reg_response.json()
    # KEY DIFFERENCE — dict .get() chain vs JS || chain (see docstring point 6)
    ctx.api_user_id = reg_body.get("userID") or reg_body.get("userId") or reg_body.get("id")

    response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/GenerateToken",
        data=ctx.api_user,
        headers={"Content-Type": "application/json"},
    )
    ctx.api_response = response
    ctx.api_response_body = await response.json()

    # KEY DIFFERENCE — isinstance() vs typeof (see docstring point 4)
    token = ctx.api_response_body.get("token") if isinstance(ctx.api_response_body, dict) else None
    ctx.api_token = token if isinstance(token, str) else None


@given("I have a valid user token")
async def have_valid_token(api_request_context: APIRequestContext, ctx: ScenarioContext) -> None:
    """Register user and generate token as precondition for authenticated requests."""
    if not ctx.api_user:
        ctx.api_user = {
            "userName": f"testuser_{int(time.time() * 1000)}",
            "password": "Password1!",
        }

    reg_response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=ctx.api_user,
        headers={"Content-Type": "application/json"},
    )
    reg_body = await reg_response.json()
    ctx.api_user_id = reg_body.get("userID") or reg_body.get("userId") or reg_body.get("id")

    token_response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/GenerateToken",
        data=ctx.api_user,
        headers={"Content-Type": "application/json"},
    )
    token_body = await token_response.json()
    token = token_body.get("token") if isinstance(token_body, dict) else None
    ctx.api_token = token if isinstance(token, str) else None


@when("I request my user account details")
async def request_user_details(api_request_context: APIRequestContext, ctx: ScenarioContext) -> None:
    """
    Authenticated GET request using Bearer token.

    KEY DIFFERENCE — f-string replaces template literal:
    TS: `Bearer ${this.apiToken!}`
    PY: f"Bearer {ctx.api_token}"
    No '!' assertion needed — we assert api_token is not None below.
    """
    assert ctx.api_token, "No API token available — run 'I have a valid user token' first"
    user_id = ctx.api_user_id or (ctx.api_user["userName"] if ctx.api_user else None)
    assert user_id, "No user ID or username available for account lookup"

    response = await api_request_context.get(
        f"{BASE_URL}/Account/v1/User/{user_id}",
        headers={"Authorization": f"Bearer {ctx.api_token}"},
    )
    ctx.api_response = response
    ctx.api_response_body = await response.json()


@then("the response should have status 200")
def check_status_200(ctx: ScenarioContext) -> None:
    """
    CRITICAL KEY DIFFERENCE:
    TS: expect(this.apiResponse!.status()).toBe(200)  — status() is a METHOD CALL
    PY: assert ctx.api_response.status == 200         — status is a PROPERTY

    If you write ctx.api_response.status() in Python, it returns a bound method object.
    A bound method is always truthy — the assertion would never fail even on 404/500.
    This silent bug is the #1 Playwright porting mistake from TypeScript to Python.
    """
    assert ctx.api_response is not None, "No API response stored in context"
    assert ctx.api_response.status == 200, f"Expected 200, got {ctx.api_response.status}"


@then("the response should contain a list of books")
def check_books_list(ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — isinstance() vs Array.isArray():
    TS: expect(Array.isArray(body.books)).toBe(true)
    PY: assert isinstance(body["books"], list)
    isinstance() checks the runtime type — equivalent to Array.isArray() for list types.
    """
    assert isinstance(ctx.api_response_body, dict), "Response body is not a dict"
    assert isinstance(ctx.api_response_body.get("books"), list), "Response body has no 'books' list"


@then("the response should contain a token")
def check_token(ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — typeof vs isinstance():
    TS: expect(typeof this.apiToken).toBe('string')
    PY: assert isinstance(ctx.api_token, str)
    """
    assert isinstance(ctx.api_token, str), f"Expected a string token, got: {ctx.api_token!r}"
    assert len(ctx.api_token) > 10, f"Token too short: '{ctx.api_token}'"


@then("the response should contain my user information")
def check_user_info(ctx: ScenarioContext) -> None:
    """
    KEY DIFFERENCE — dict access vs object property:
    TS: expect(body.username || body.userName).toBe(this.apiUser!.userName)
    PY: assert body.get("username") or body.get("userName") == ctx.api_user["userName"]
    """
    assert isinstance(ctx.api_response_body, dict), "Response body is not a dict"
    assert ctx.api_user is not None
    returned_name = ctx.api_response_body.get("username") or ctx.api_response_body.get("userName")
    assert returned_name == ctx.api_user["userName"], f"Expected '{ctx.api_user['userName']}', got '{returned_name}'"
