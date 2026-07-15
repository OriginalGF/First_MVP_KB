import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "ai-test.db"
    monkeypatch.setenv("PROJECT_MGMT_DB_PATH", str(db_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    import backend.app.main as main_module

    module = importlib.reload(main_module)
    return TestClient(module.app)


def test_ai_health_returns_configured_status(client):
    response = client.get("/api/ai/health")

    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_ai_prompt_returns_response_when_provider_is_available(monkeypatch, client):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(*args, **kwargs):
        return FakeResponse({
            "choices": [{"message": {"content": "4"}}],
        })

    monkeypatch.setattr("backend.app.main.httpx.post", fake_post)

    response = client.post(
        "/api/ai/test",
        json={"prompt": "What is 2 + 2?"},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "4"
