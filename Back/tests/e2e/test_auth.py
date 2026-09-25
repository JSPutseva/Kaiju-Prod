from fastapi.testclient import TestClient


def test_register_login_and_get_me(
    client: TestClient,
):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E User",
            "email": "e2e-auth@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    registered_user = register_response.json()

    assert registered_user["name"] == "E2E User"
    assert registered_user["email"] == "e2e-auth@example.com"
    assert registered_user["role"] is None

    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-auth@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert login_data["token_type"] == "bearer"
    assert login_data["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                f"Bearer {login_data['access_token']}"
            )
        },
    )

    assert me_response.status_code == 200

    current_user = me_response.json()

    assert current_user["id"] == registered_user["id"]
    assert current_user["name"] == "E2E User"
    assert current_user["email"] == "e2e-auth@example.com"