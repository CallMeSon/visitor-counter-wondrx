from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_static_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "Event Visitor Counter Dashboard" in response.text
