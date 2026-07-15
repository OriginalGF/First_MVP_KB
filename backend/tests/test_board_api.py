import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("PROJECT_MGMT_DB_PATH", str(db_path))

    import backend.app.main as main_module

    module = importlib.reload(main_module)
    return TestClient(module.app)


def test_get_board_initializes_default_state(client):
    response = client.get("/api/boards/user")

    assert response.status_code == 200
    payload = response.json()
    assert payload["columns"][0]["title"] == "Backlog"
    assert len(payload["cards"]) == 8


def test_create_card_and_rename_column_persists(client):
    create_response = client.post(
        "/api/boards/user/cards",
        json={
            "columnId": "col-backlog",
            "title": "Write release notes",
            "details": "Capture launch details",
        },
    )

    assert create_response.status_code == 200
    created_board = create_response.json()
    created_card_id = next(
        card_id
        for card_id, card in created_board["cards"].items()
        if card["title"] == "Write release notes"
    )
    assert created_card_id in created_board["columns"][0]["cardIds"]

    rename_response = client.patch(
        "/api/boards/user/columns/col-backlog",
        json={"title": "Next Up"},
    )

    assert rename_response.status_code == 200
    assert rename_response.json()["columns"][0]["title"] == "Next Up"

    persisted_response = client.get("/api/boards/user")
    assert persisted_response.json()["columns"][0]["title"] == "Next Up"


def test_delete_card_removes_card_from_board(client):
    create_response = client.post(
        "/api/boards/user/cards",
        json={
            "columnId": "col-backlog",
            "title": "Delete me",
            "details": "Will be removed",
        },
    )
    card_id = next(
        card_id
        for card_id, card in create_response.json()["cards"].items()
        if card["title"] == "Delete me"
    )

    delete_response = client.delete(f"/api/boards/user/cards/{card_id}", params={"columnId": "col-backlog"})

    assert delete_response.status_code == 200
    board = delete_response.json()
    assert card_id not in board["cards"]
    assert card_id not in board["columns"][0]["cardIds"]


def test_put_board_persists_full_board_state(client):
    updated_board = {
        "columns": [
            {"id": "col-backlog", "title": "Ready", "cardIds": []},
        ],
        "cards": {},
    }

    response = client.put("/api/boards/user", json=updated_board)

    assert response.status_code == 200
    assert response.json()["columns"][0]["title"] == "Ready"
    assert client.get("/api/boards/user").json()["columns"][0]["title"] == "Ready"
