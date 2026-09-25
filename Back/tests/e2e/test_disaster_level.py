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

    # Change Apex and Echo together, from L1 to L5.
    disaster_response = client.patch(
        "/quarters/disaster-level",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "quarter_ids": [1, 2],
            "level": 5,
        },
    )

    assert disaster_response.status_code == 200

    quarters = {q["id"]: q for q in disaster_response.json()}

    assert quarters[1]["name"] == "Apex"
    assert quarters[1]["disaster_level"] == 5
    assert quarters[2]["name"] == "Echo"
    assert quarters[2]["disaster_level"] == 5

    # the change is recorded in history, attributed to whoever triggered it
    history_response = client.get(
        "/quarters/disaster-level-events",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert history_response.status_code == 200

    events = history_response.json()
    apex_events = [e for e in events if e["quarter_id"] == 1]

    assert len(apex_events) == 1
    assert apex_events[0]["level"] == 5
    assert apex_events[0]["changed_by_id"] == user["id"]


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
        "/quarters/disaster-level",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "quarter_ids": [1],
            "level": 5,
        },
    )

    assert disaster_response.status_code == 403
