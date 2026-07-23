import os
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_logo_asset_exists():
    assert os.path.exists("src/static/assets/logo.png")

def test_logo_asset_served():
    response = client.get("/assets/logo.png")
    assert response.status_code == 200
    assert response.headers["content-type"] in ["image/png", "image/x-png"]
