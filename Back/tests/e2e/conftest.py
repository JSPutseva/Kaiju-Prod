import os

# Must be set before importing app.database because the application
# creates its SQLAlchemy engine when the module is imported.
os.environ["DATABASE_URL"] = "sqlite:///./test_e2e.db"
os.environ["JWT_SECRET_KEY"] = "e2e-test-secret"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.resource_type import ResourceType


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as db:
        quarters = [
            Quarter(
                id=1,
                name="Apex",
                disaster_level=1,
                sea_access=False,
            ),
            Quarter(
                id=2,
                name="Echo",
                disaster_level=1,
                sea_access=True,
            ),
            Quarter(
                id=3,
                name="Warden",
                disaster_level=1,
                sea_access=False,
            ),
            Quarter(
                id=4,
                name="Xeno",
                disaster_level=1,
                sea_access=True,
            ),
            Quarter(
                id=5,
                name="Zion",
                disaster_level=1,
                sea_access=True,
            ),
        ]

        resource_types = [
            ResourceType(
                id=1,
                name="Medical personnel",
                description="Medical personnel",
            ),
            ResourceType(
                id=2,
                name="Rescue teams",
                description="Rescue teams",
            ),
        ]

        db.add_all(quarters)
        db.add_all(resource_types)
        db.commit()

        resources = [
            QuarterResource(
                quarter_id=1,
                resource_type_id=1,
                initial_quantity=12,
                available_quantity=12,
                reserved_quantity=0,
            ),
            QuarterResource(
                quarter_id=2,
                resource_type_id=1,
                initial_quantity=5,
                available_quantity=5,
                reserved_quantity=0,
            ),
            QuarterResource(
                quarter_id=3,
                resource_type_id=1,
                initial_quantity=8,
                available_quantity=8,
                reserved_quantity=0,
            ),
            QuarterResource(
                quarter_id=4,
                resource_type_id=1,
                initial_quantity=3,
                available_quantity=3,
                reserved_quantity=0,
            ),
            QuarterResource(
                quarter_id=5,
                resource_type_id=1,
                initial_quantity=7,
                available_quantity=7,
                reserved_quantity=0,
            ),
        ]

        db.add_all(resources)
        db.commit()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def register_user(client: TestClient):
    def _register(
        name: str,
        email: str,
        password: str = "password123",
        role: str | None = None,
        quarter_id: int | None = None,
    ) -> dict:
        payload = {
            "name": name,
            "email": email,
            "password": password,
        }

        if role is not None:
            payload["role"] = role

        if quarter_id is not None:
            payload["quarter_id"] = quarter_id

        response = client.post(
            "/auth/register",
            json=payload,
        )

        assert response.status_code == 201, response.text

        return response.json()

    return _register


@pytest.fixture()
def login_user(client: TestClient):
    def _login(
        email: str,
        password: str = "password123",
    ) -> dict:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert response.status_code == 200, response.text

        return response.json()

    return _login


@pytest.fixture()
def auth_headers(login_user):
    def _headers(
        email: str,
        password: str = "password123",
    ) -> dict:
        login_response = login_user(
            email=email,
            password=password,
        )

        return {
            "Authorization": (
                f"Bearer {login_response['access_token']}"
            )
        }

    return _headers