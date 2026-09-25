import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app
from app.models.organization import Organization
from app.models.user import User
from app.devices.validation import normalize_identifier, normalize_imei, validate_imei


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def make_user_and_org():
    db = TestingSessionLocal()

    organization = Organization(
        name=f"Device Test {uuid.uuid4()}",
        slug=f"device-test-{uuid.uuid4()}",
        is_active=True,
    )

    user = User(
        email=f"{uuid.uuid4()}@example.com",
        password_hash="test-hash",
        is_active=True,
    )

    db.add_all([organization, user])
    db.commit()
    db.refresh(organization)
    db.refresh(user)

    db.close()

    return organization, user


def test_identifier_normalization():
    assert normalize_identifier("  abc-123  ") == "ABC-123"
    assert normalize_identifier("") is None
    assert normalize_identifier(None) is None


def test_imei_normalization():
    assert normalize_imei(" 490154203237518 ") == "490154203237518"


def test_imei_luhn_validation():
    assert validate_imei("490154203237518") is True
    assert validate_imei("490154203237517") is False


def test_device_schema_imports():
    from app.devices.schemas import DeviceRecordCreate, DeviceRecordResponse

    assert DeviceRecordCreate is not None
    assert DeviceRecordResponse is not None


def test_device_routes_registered():
    from app.api.devices.routes import router

    paths = {
        route.path
        for route in router.routes
        if hasattr(route, "path")
    }

    assert "/devices" in paths
    assert "/devices/search" in paths
    assert "/devices/lookup/imei/{imei}" in paths
    assert "/devices/lookup/serial/{serial_number}" in paths
    assert "/devices/lookup/barcode/{barcode}" in paths
    assert "/devices/{device_id}" in paths


def test_device_model_imports():
    from app.devices.models import DeviceRecord

    assert DeviceRecord.__tablename__ == "device_records"
