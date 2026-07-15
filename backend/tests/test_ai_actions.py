import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "ai-actions.db"
    monkeypatch.setenv("PROJECT_MGMT_DB_PATH", str(db_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    import backend.app.main as main_module

    module = importlib.reload(main_module)
    return TestClient(module.app)


def test_structured_ai_action_returns_message_and_updates(monkeypatch, client):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(*args, **kwargs):
        return FakeResponse({
            "choices": [{"message": {"content": '{"message":"Card updated","updates":[{"type":"rename-column","columnId":"col-backlog","title":"Ready"}]}'}}],
        })

    monkeypatch.setattr("backend.app.main.httpx.post", fake_post)

    response = client.post(
        "/api/ai/action",
        json={
            "prompt": "Rename the backlog column to Ready",
            "board": {
                "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": []}],
                "cards": {},
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Card updated"
    assert payload["board"]["columns"][0]["title"] == "Ready"
