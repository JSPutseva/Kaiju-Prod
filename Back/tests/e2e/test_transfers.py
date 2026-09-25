from fastapi.testclient import TestClient


def register_and_login(
    client: TestClient,
    name: str,
    email: str,
) -> tuple[dict, str]:
    register_response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "password123",
        },
    )

    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return user, token


def assign_role(
    client: TestClient,
    user_id: int,
    token: str,
    role: str,
    quarter_ids: list[int],
) -> None:
    response = client.patch(
        f"/users/{user_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": role,
            "quarter_ids": quarter_ids,
        },
    )

    assert response.status_code == 200


def test_qc_cannot_request_transfer_before_level_3(
    client: TestClient,
):
    user, token = register_and_login(
        client,
        "E2E Transfer QC L1",
        "e2e-transfer-qc-l1@example.com",
    )

    assign_role(
        client,
        user["id"],
        token,
        "QC",
        [1],
    )

    # /transfers/route is a preview endpoint: an illegal route is still a
    # 200 with ok: false and a reason, not an HTTP error
    response = client.post(
        "/transfers/route",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_quarter_id": 1,
            "destination_quarter_id": 2,
            "resource_type_id": 1,
            "quantity": 1,
        },
    )

    assert response.status_code == 200

    decision = response.json()

    assert decision["ok"] is False
    assert decision["reason"] == "DISASTER_LEVEL_TOO_LOW"


def test_qc_can_request_valid_adjacent_transfer_at_level_3(
    client: TestClient,
):
    qc_user, qc_token = register_and_login(
        client,
        "E2E Transfer QC L3",
        "e2e-transfer-qc-l3@example.com",
    )

    assign_role(
        client,
        qc_user["id"],
        qc_token,
        "QC",
        [1],
    )

    cd_user, cd_token = register_and_login(
        client,
        "E2E Transfer CD L3",
        "e2e-transfer-cd-l3@example.com",
    )

    assign_role(
        client,
        cd_user["id"],
        cd_token,
        "CD",
        [],
    )

    disaster_response = client.patch(
        "/quarters/disaster-level",
        headers={"Authorization": f"Bearer {cd_token}"},
        json={"quarter_ids": [1], "level": 3},
    )

    assert disaster_response.status_code == 200
    assert disaster_response.json()[0]["disaster_level"] == 3

    response = client.post(
        "/transfers/route",
        headers={"Authorization": f"Bearer {qc_token}"},
        json={
            "source_quarter_id": 1,
            "destination_quarter_id": 2,
            "resource_type_id": 1,
            "quantity": 1,
        },
    )

    assert response.status_code == 200

    decision = response.json()

    assert decision["ok"] is True
    assert decision["route_type"] == "direct"
    assert decision["transit_via"] is None
    assert decision["reason"] == "ALLOWED"


def test_cd_cannot_request_adjacent_transfer_at_level_4(
    client: TestClient,
):
    user, token = register_and_login(
        client,
        "E2E Transfer CD L4",
        "e2e-transfer-cd-l4@example.com",
    )

    assign_role(
        client,
        user["id"],
        token,
        "CD",
        [],
    )

    disaster_response = client.patch(
        "/quarters/disaster-level",
        headers={"Authorization": f"Bearer {token}"},
        json={"quarter_ids": [1], "level": 4},
    )

    assert disaster_response.status_code == 200

    # per the permission matrix, "request adjacent transfer" at level 4 is
    # QC/LC only — CD's level-4 power is requisition, not this action
    response = client.post(
        "/transfers/route",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_quarter_id": 1,
            "destination_quarter_id": 2,
            "resource_type_id": 1,
            "quantity": 1,
        },
    )

    assert response.status_code == 200

    decision = response.json()

    assert decision["ok"] is False
    assert decision["reason"] == "PERMISSION_DENIED"


def test_qc_cannot_organize_transit_at_level_3(
    client: TestClient,
):
    qc_user, qc_token = register_and_login(
        client,
        "E2E Transit QC",
        "e2e-transit-qc@example.com",
    )

    assign_role(
        client,
        qc_user["id"],
        qc_token,
        "QC",
        [1],
    )

    cd_user, cd_token = register_and_login(
        client,
        "E2E Transit CD",
        "e2e-transit-cd@example.com",
    )

    assign_role(
        client,
        cd_user["id"],
        cd_token,
        "CD",
        [],
    )

    disaster_response = client.patch(
        "/quarters/disaster-level",
        headers={"Authorization": f"Bearer {cd_token}"},
        json={"quarter_ids": [1], "level": 3},
    )

    assert disaster_response.status_code == 200

    # transit doesn't exist below disaster level 4 at all, regardless of role
    response = client.post(
        "/transfers/route",
        headers={"Authorization": f"Bearer {qc_token}"},
        json={
            "source_quarter_id": 1,
            "destination_quarter_id": 5,
            "resource_type_id": 1,
            "quantity": 1,
            "transit_via": 4,
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False
