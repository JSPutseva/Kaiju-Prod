from fastapi.testclient import TestClient


def test_city_director_can_change_disaster_level(
    client: TestClient,
):
    # Create the first user.
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E Disaster Director",
            "email": "e2e-disaster-cd@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    user = register_response.json()

    # Bootstrap the first City Director.
    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-disaster-cd@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    role_response = client.patch(
        f"/users/{user['id']}/role",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "role": "CD",
            "quarter_ids": [],
        },
    )

    assert role_response.status_code == 200

    # Change Apex from L1 to L5.
    disaster_response = client.patch(
        "/quarters/1/disaster-level",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "level": 5,
        },
    )

    assert disaster_response.status_code == 200

    quarter = disaster_response.json()

    assert quarter["id"] == 1
    assert quarter["name"] == "Apex"
    assert quarter["disaster_level"] == 5


def test_non_city_director_cannot_change_disaster_level(
    client: TestClient,
):
    # Create a user.
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E QC",
            "email": "e2e-disaster-qc@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    user = register_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-disaster-qc@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Bootstrap as QC.
    role_response = client.patch(
        f"/users/{user['id']}/role",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "role": "QC",
            "quarter_ids": [1],
        },
    )

    assert role_response.status_code == 200

    # QC must not be allowed to change the disaster level.
    disaster_response = client.patch(
        "/quarters/1/disaster-level",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "level": 5,
        },
    )

    assert disaster_response.status_code == 403