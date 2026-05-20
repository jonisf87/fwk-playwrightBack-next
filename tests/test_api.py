"""
Native Playwright API tests — no BDD/Gherkin layer.
BDD branch equivalent: tests/steps/api_steps.py + tests/features/api.feature

KEY DIFFERENCES vs BDD branch:

  1. No Gherkin — test intent is expressed in the function name and asserts,
     not in Given/When/Then sentences. Simpler for pure unit/integration tests.

  2. async def test_* — every test is a coroutine; pytest-asyncio runs it
     via asyncio_mode = "auto" set in pyproject.toml.
     BDD:    def have_valid_credentials(ctx): ...  (sync step)
     Native: async def test_retrieve_all_books(api_request_context): ...

  3. await on every network call:
     BDD:    response = api_request_context.get(url)   (sync)
     Native: response = await api_request_context.get(url)  (async)

  4. response.status is still a PROPERTY (not a method) in both APIs:
     assert response.status == 200  — same in sync and async Playwright
     This is the #1 porting bug from TypeScript (where status() is a method).

  5. response.json() must be awaited in async_api:
     BDD:    body = response.json()         (sync, no await)
     Native: body = await response.json()   (async coroutine)
"""

import time

import pytest
from playwright.async_api import APIRequestContext

BASE_URL = "https://demoqa.com"


@pytest.mark.api
async def test_retrieve_all_books(api_request_context: APIRequestContext) -> None:
    response = await api_request_context.get(f"{BASE_URL}/BookStore/v1/Books")
    assert response.status == 200
    body = await response.json()
    assert isinstance(body.get("books"), list)


@pytest.mark.api
async def test_generate_user_token(api_request_context: APIRequestContext) -> None:
    """
    KEY DIFFERENCE — await response.json():
    BDD:    body = response.json()
    Native: body = await response.json()
    """
    credentials = {
        "userName": f"testuser_{int(time.time() * 1000)}",
        "password": "Password1!",
    }
    await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    response = await api_request_context.post(
        f"{BASE_URL}/Account/v1/GenerateToken",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    assert response.status == 200
    body = await response.json()
    token = body.get("token") if isinstance(body, dict) else None
    assert isinstance(token, str) and len(token) > 10


@pytest.mark.api
async def test_authenticated_user_details(api_request_context: APIRequestContext) -> None:
    credentials = {
        "userName": f"testuser_{int(time.time() * 1000)}",
        "password": "Password1!",
    }
    reg = await api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    reg_body = await reg.json()
    user_id = reg_body.get("userID") or reg_body.get("userId")

    token_resp = await api_request_context.post(
        f"{BASE_URL}/Account/v1/GenerateToken",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    token_body = await token_resp.json()
    token = token_body.get("token")

    response = await api_request_context.get(
        f"{BASE_URL}/Account/v1/User/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status == 200
    body = await response.json()
    returned_name = body.get("username") or body.get("userName")
    assert returned_name == credentials["userName"]
