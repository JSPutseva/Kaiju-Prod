from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def test_qc_can_create_and_read_resource_request(
    client: TestClient,
):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E Request QC",
            "email": "e2e-request-qc@example.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-request-qc@example.com",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    role_response = client.patch(
        f"/users/{user['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": "QC",
            "quarter_ids": [1],
        },
    )
    assert role_response.status_code == 200

    # Inter-quarter requests require at least disaster level 3.
    cd_register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E Request CD",
            "email": "e2e-request-cd@example.com",
            "password": "password123",
        },
    )
    assert cd_register_response.status_code == 201
    cd_user = cd_register_response.json()

    cd_login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-request-cd@example.com",
            "password": "password123",
        },
    )
    assert cd_login_response.status_code == 200
    cd_token = cd_login_response.json()["access_token"]

    cd_role_response = client.patch(
        f"/users/{cd_user['id']}/role",
        headers={"Authorization": f"Bearer {cd_token}"},
        json={
            "role": "CD",
            "quarter_ids": [],
        },
    )
    assert cd_role_response.status_code == 200

    disaster_response = client.patch(
        "/quarters/1/disaster-level",
        headers={"Authorization": f"Bearer {cd_token}"},
        json={"level": 3},
    )
    assert disaster_response.status_code == 200
    assert disaster_response.json()["disaster_level"] == 3

    request_response = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_quarter_id": 1,
            "destination_quarter_id": 2,
            "resource_type_id": 1,
            "quantity": 1,
        },
    )

    assert request_response.status_code == 201
    created_request = request_response.json()

    assert created_request["requester_id"] == user["id"]
    assert created_request["source_quarter_id"] == 1
    assert created_request["destination_quarter_id"] == 2
    assert created_request["resource_type_id"] == 1
    assert created_request["quantity"] == 1
    assert created_request["status"] == "PENDING"

    request_id = created_request["id"]

    get_response = client.get(
        f"/requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 200
    fetched_request = get_response.json()

    assert fetched_request["id"] == request_id
    assert fetched_request["quantity"] == 1
    assert fetched_request["status"] == "PENDING"


def test_user_without_role_cannot_create_resource_request(
    client: TestClient,
):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E No Role",
            "email": "e2e-request-no-role@example.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-request-no-role@example.com",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    request_response = client.post(
        "/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_quarter_id": 1,
            "destination_quarter_id": 2,
            "resource_type_id": 1,
            "quantity": 1,
        },
    )

    assert request_response.status_code == 403
    assert request_response.json()["detail"]["code"] == "NO_ROLE_ASSIGNED"


def test_qc_can_create_and_cancel_reservation(
    client: TestClient,
):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E Reservation QC",
            "email": "e2e-reservation-qc@example.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-reservation-qc@example.com",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    role_response = client.patch(
        f"/users/{user['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": "QC",
            "quarter_ids": [1],
        },
    )
    assert role_response.status_code == 200

    # Reservations require disaster level 2 or higher.
    cd_register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E Reservation CD",
            "email": "e2e-reservation-cd@example.com",
            "password": "password123",
        },
    )
    assert cd_register_response.status_code == 201
    cd_user = cd_register_response.json()

    cd_login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-reservation-cd@example.com",
            "password": "password123",
        },
    )
    assert cd_login_response.status_code == 200
    cd_token = cd_login_response.json()["access_token"]

    cd_role_response = client.patch(
        f"/users/{cd_user['id']}/role",
        headers={"Authorization": f"Bearer {cd_token}"},
        json={
            "role": "CD",
            "quarter_ids": [],
        },
    )
    assert cd_role_response.status_code == 200

    disaster_response = client.patch(
        "/quarters/1/disaster-level",
        headers={"Authorization": f"Bearer {cd_token}"},
        json={"level": 2},
    )
    assert disaster_response.status_code == 200
    assert disaster_response.json()["disaster_level"] == 2

    start_at = datetime.now(timezone.utc) + timedelta(hours=1)
    end_at = start_at + timedelta(hours=2)

    reservation_response = client.post(
        "/reservations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "quarter_id": 1,
            "resource_type_id": 1,
            "quantity": 1,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
    )

    assert reservation_response.status_code == 201
    reservation = reservation_response.json()

    assert reservation["quarter_id"] == 1
    assert reservation["resource_type_id"] == 1
    assert reservation["user_id"] == user["id"]
    assert reservation["quantity"] == 1
    assert reservation["status"] == "APPROVED"

    reservation_id = reservation["id"]

    cancel_response = client.delete(
        f"/reservations/{reservation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert cancel_response.status_code == 200
    cancelled_reservation = cancel_response.json()

    assert cancelled_reservation["id"] == reservation_id
    assert cancelled_reservation["status"] == "CANCELLED"


def test_non_qc_cannot_create_reservation(
    client: TestClient,
):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "E2E Reservation Non QC",
            "email": "e2e-reservation-non-qc@example.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "e2e-reservation-non-qc@example.com",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    role_response = client.patch(
        f"/users/{user['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": "CD",
            "quarter_ids": [],
        },
    )
    assert role_response.status_code == 200

    start_at = datetime.now(timezone.utc) + timedelta(hours=1)
    end_at = start_at + timedelta(hours=2)

    reservation_response = client.post(
        "/reservations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "quarter_id": 1,
            "resource_type_id": 1,
            "quantity": 1,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
    )

    assert reservation_response.status_code == 403
    assert (
        reservation_response.json()["detail"]["code"]
        == "PERMISSION_DENIED"
    )
