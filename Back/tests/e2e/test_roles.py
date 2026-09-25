from fastapi.testclient import TestClient


def test_city_director_can_assign_role(
    client: TestClient,
):
    # Create the first user.
    cd_register = client.post(
        "/auth/register",
        json={
            "name": "E2E Director",
            "email": "e2e-director@example.com",
            "password": "password123",
        },
    )

    assert cd_register.status_code == 201

    cd_user = cd_register.json()

    # Bootstrap the first City Director.
    # The application allows the first role assignment when
    # no City Director exists yet.
    bootstrap_login = client.post(
        "/auth/login",
        json={
            "email": "e2e-director@example.com",
            "password": "password123",
        },
    )

    assert bootstrap_login.status_code == 200

    bootstrap_token = bootstrap_login.json()["access_token"]

    bootstrap_response = client.patch(
        f"/users/{cd_user['id']}/role",
        headers={
            "Authorization": f"Bearer {bootstrap_token}",
        },
        json={
            "role": "CD",
            "quarter_ids": [],
        },
    )

    assert bootstrap_response.status_code == 200

    assigned_cd = bootstrap_response.json()

    assert assigned_cd["role"] == "CD"
    assert assigned_cd["quarter_ids"] == []

    # Create a second user.
    qc_register = client.post(
        "/auth/register",
        json={
            "name": "E2E Coordinator",
            "email": "e2e-qc@example.com",
            "password": "password123",
        },
    )

    assert qc_register.status_code == 201

    qc_user = qc_register.json()

    # Login as the City Director.
    cd_login = client.post(
        "/auth/login",
        json={
            "email": "e2e-director@example.com",
            "password": "password123",
        },
    )

    assert cd_login.status_code == 200

    cd_token = cd_login.json()["access_token"]

    # Assign QC role to the second user and scope it to Apex.
    role_response = client.patch(
        f"/users/{qc_user['id']}/role",
        headers={
            "Authorization": f"Bearer {cd_token}",
        },
        json={
            "role": "QC",
            "quarter_ids": [1],
        },
    )

    assert role_response.status_code == 200

    assigned_qc = role_response.json()

    assert assigned_qc["id"] == qc_user["id"]
    assert assigned_qc["role"] == "QC"
    assert assigned_qc["quarter_ids"] == [1]