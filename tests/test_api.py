"""
Native Playwright API tests using pytest-playwright.

KEY DIFFERENCE vs feature/native-playwright:
  That branch: async def test_* + await response.json()
  This branch:      def test_* +       response.json()  (sync — no await)

pytest-playwright provides api_request_context as a sync fixture.
response.status is still a PROPERTY (not a method) in both sync and async APIs.
"""

import time

import pytest
from playwright.sync_api import APIRequestContext

BASE_URL = "https://demoqa.com"


@pytest.mark.api
def test_retrieve_all_books(api_request_context: APIRequestContext) -> None:
    response = api_request_context.get(f"{BASE_URL}/BookStore/v1/Books")
    assert response.status == 200
    body = response.json()
    assert isinstance(body.get("books"), list)


@pytest.mark.api
def test_generate_user_token(api_request_context: APIRequestContext) -> None:
    credentials = {
        "userName": f"testuser_{int(time.time() * 1000)}",
        "password": "Password1!",
    }
    api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    response = api_request_context.post(
        f"{BASE_URL}/Account/v1/GenerateToken",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    assert response.status == 200
    body = response.json()
    token = body.get("token") if isinstance(body, dict) else None
    assert isinstance(token, str) and len(token) > 10


@pytest.mark.api
def test_authenticated_user_details(api_request_context: APIRequestContext) -> None:
    credentials = {
        "userName": f"testuser_{int(time.time() * 1000)}",
        "password": "Password1!",
    }
    reg = api_request_context.post(
        f"{BASE_URL}/Account/v1/User",
        data=credentials,
        headers={"Content-Type": "application/json"},
    )
    reg_body = reg.json()
    user_id = reg_body.get("userID") or reg_body.get("userId")

    token_body = api_request_context.post(
        f"{BASE_URL}/Account/v1/GenerateToken",
        data=credentials,
        headers={"Content-Type": "application/json"},
    ).json()
    token = token_body.get("token")

    response = api_request_context.get(
        f"{BASE_URL}/Account/v1/User/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status == 200
    body = response.json()
    returned_name = body.get("username") or body.get("userName")
    assert returned_name == credentials["userName"]
