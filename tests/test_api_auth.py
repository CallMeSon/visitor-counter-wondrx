import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.db.database import Base, get_db
from src.db.models import Event, CameraConfig

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(Event(id=1, name="Test Event", max_capacity=1000))
    db.add(CameraConfig(id=1, event_id=1, name="Pintu 1", role="entry"))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_api_count_without_key_when_env_set(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    response = client.post("/api/count", json={"event_id": 1, "camera_id": 1, "count": 1})
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json()["detail"]

def test_api_count_with_invalid_key_when_env_set(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    response = client.post(
        "/api/count",
        json={"event_id": 1, "camera_id": 1, "count": 1},
        headers={"X-API-Key": "wrongkey"}
    )
    assert response.status_code == 401

def test_api_count_with_valid_key_when_env_set(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    response = client.post(
        "/api/count",
        json={"event_id": 1, "camera_id": 1, "count": 1},
        headers={"X-API-Key": "secret123"}
    )
    assert response.status_code == 200

def test_api_count_when_env_unset(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    response = client.post("/api/count", json={"event_id": 1, "camera_id": 1, "count": 1})
    assert response.status_code == 200
