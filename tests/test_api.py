import os

import pytest
from fastapi.testclient import TestClient

if not os.getenv("GEMINI_API_KEY"):
    pytest.skip(
        "GEMINI_API_KEY is required for AI integration tests.",
        allow_module_level=True,
    )

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ai"] == "gemini"


def test_chat():
    response = client.post(
        "/api/chat",
        json={
            "session_id": "test-session",
            "message": "I am looking for a 3 BHK with a budget of 1.5 crore.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "reply" in data
    assert data["lead"]["configuration"] == "3 BHK"
    assert data["lead"]["budget"] == "₹1.5 crore"


def test_reset():
    response = client.post(
        "/api/reset",
        json={"session_id": "test-session"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
