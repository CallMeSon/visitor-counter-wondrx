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

def test_analytics_html_and_js_served():
    res_html = client.get("/analytics.html")
    assert res_html.status_code == 200
    assert "Laporan Pengunjung Multi-Hari" in res_html.text

    res_js = client.get("/analytics.js")
    assert res_js.status_code == 200

