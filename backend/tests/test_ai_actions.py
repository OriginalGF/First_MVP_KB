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


def test_structured_ai_action_can_rename_card(monkeypatch, client):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(*args, **kwargs):
        return FakeResponse({
            "choices": [{"message": {"content": '{"message":"Renamed card","updates":[{"type":"rename-card","cardId":"card-1","title":"Updated title"}]}'}}],
        })

    monkeypatch.setattr("backend.app.main.httpx.post", fake_post)

    response = client.post(
        "/api/ai/action",
        json={
            "prompt": "Rename this card",
            "board": {
                "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]}],
                "cards": {"card-1": {"id": "card-1", "title": "Old title", "details": ""}},
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Renamed card"
    assert payload["board"]["cards"]["card-1"]["title"] == "Updated title"


def test_plain_text_ai_response_is_returned_without_fallback(monkeypatch, client):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(*args, **kwargs):
        return FakeResponse({
            "choices": [{"message": {"content": "Hello there, how can I help with your board today?"}}],
        })

    monkeypatch.setattr("backend.app.main.httpx.post", fake_post)

    response = client.post(
        "/api/ai/action",
        json={
            "prompt": "hello",
            "board": {
                "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": []}],
                "cards": {},
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"].startswith("Hello there")


def test_plain_text_ai_response_still_applies_rename_fallback(monkeypatch, client):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(*args, **kwargs):
        return FakeResponse({
            "choices": [{"message": {"content": "Sure, I can do that."}}],
        })

    monkeypatch.setattr("backend.app.main.httpx.post", fake_post)

    response = client.post(
        "/api/ai/action",
        json={
            "prompt": "rename backlog to Ready",
            "board": {
                "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": []}],
                "cards": {},
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["board"]["columns"][0]["title"] == "Ready"
