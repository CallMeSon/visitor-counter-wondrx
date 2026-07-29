import os
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

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
