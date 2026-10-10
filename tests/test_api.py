"""Tests for FastAPI backend endpoints, security headers, and rate limiting."""

from fastapi.testclient import TestClient
from api import app
from tests.test_mock_pipeline import create_dummy_png_bytes

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["model_name"] == "gemini-3.5-flash-lite"
    assert data["model_provider"] == "google"


def test_security_headers():
    resp = client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"


def test_index_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "Utility Bill Decoder" in resp.text


def test_upload_rejection_on_invalid_file():
    # Sending text file as bill
    files = {"file": ("test.txt", b"plain text", "text/plain")}
    resp = client.post("/api/decode", files=files)
    assert resp.status_code == 400
    assert "Invalid image format" in resp.json()["detail"]
