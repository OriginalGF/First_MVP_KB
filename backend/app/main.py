import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_BUILD_DIR = ROOT_DIR / "frontend" / "out"
DB_PATH = Path(os.getenv("PROJECT_MGMT_DB_PATH", ROOT_DIR / "backend" / "app" / "project_management.db"))

app = FastAPI(title="Project Management MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3001",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CardPayload(BaseModel):
    columnId: str
    title: str
    details: str


class ColumnUpdatePayload(BaseModel):
    title: str


class MovePayload(BaseModel):
    fromColumnId: str
    toColumnId: str
    cardId: str


class AIRequestPayload(BaseModel):
    prompt: str


class AIActionPayload(BaseModel):
    prompt: str
    board: dict[str, Any]


def initialize_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS boards (
                user_id TEXT PRIMARY KEY,
                board_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


initialize_db()


def load_board(user_id: str) -> dict[str, Any]:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT board_json FROM boards WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row is None:
            default_board = {
                "columns": [
                    {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
                    {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
                    {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
                    {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
                    {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
                ],
                "cards": {
                    "card-1": {"id": "card-1", "title": "Align roadmap themes", "details": "Draft quarterly themes with impact statements and metrics."},
                    "card-2": {"id": "card-2", "title": "Gather customer signals", "details": "Review support tags, sales notes, and churn feedback."},
                    "card-3": {"id": "card-3", "title": "Prototype analytics view", "details": "Sketch initial dashboard layout and key drill-downs."},
                    "card-4": {"id": "card-4", "title": "Refine status language", "details": "Standardize column labels and tone across the board."},
                    "card-5": {"id": "card-5", "title": "Design card layout", "details": "Add hierarchy and spacing for scanning dense lists."},
                    "card-6": {"id": "card-6", "title": "QA micro-interactions", "details": "Verify hover, focus, and loading states."},
                    "card-7": {"id": "card-7", "title": "Ship marketing page", "details": "Final copy approved and asset pack delivered."},
                    "card-8": {"id": "card-8", "title": "Close onboarding sprint", "details": "Document release notes and share internally."},
                },
            }
            save_board(user_id, default_board)
            return default_board

        import json

        return json.loads(row[0])


def save_board(user_id: str, board: dict[str, Any]) -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO boards (user_id, board_json) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET board_json = excluded.board_json",
            (user_id, __import__("json").dumps(board)),
        )
        connection.commit()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "project-management-mvp"}


@app.get("/api/ai/health")
def ai_health() -> dict[str, bool]:
    return {"ready": bool(os.getenv("OPENROUTER_API_KEY"))}


@app.post("/api/ai/test")
def ai_test(payload: AIRequestPayload) -> dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenRouter API key is not configured")

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": payload.prompt}],
        },
        timeout=20.0,
    )
    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"]
    return {"reply": reply}


@app.post("/api/ai/action")
def ai_action(payload: AIActionPayload) -> dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenRouter API key is not configured")

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a project management assistant. Respond with a JSON object containing a message string and an optional updates array. Supported update types: rename-column, add-card, delete-card, move-card. Each update must include a type and the fields needed for that action.",
                },
                {
                    "role": "user",
                    "content": f"User request: {payload.prompt}\n\nBoard JSON:\n{payload.board}",
                },
            ],
        },
        timeout=20.0,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    try:
        parsed = __import__("json").loads(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="AI response was not valid JSON") from exc

    message = parsed.get("message", "")
    updates = parsed.get("updates", [])
    if not isinstance(message, str) or not isinstance(updates, list):
        raise HTTPException(status_code=400, detail="AI response did not match the expected shape")

    board = payload.board
    for update in updates:
        if update.get("type") == "rename-column":
            column_id = update.get("columnId")
            title = update.get("title")
            if not isinstance(column_id, str) or not isinstance(title, str):
                raise HTTPException(status_code=400, detail="Invalid rename-column update")
            for column in board.get("columns", []):
                if column.get("id") == column_id:
                    column["title"] = title
                    break
        elif update.get("type") == "add-card":
            column_id = update.get("columnId")
            title = update.get("title")
            details = update.get("details", "")
            if not isinstance(column_id, str) or not isinstance(title, str):
                raise HTTPException(status_code=400, detail="Invalid add-card update")
            card_id = f"card-{len(board.get('cards', {})) + 1}"
            board.setdefault("cards", {})[card_id] = {"id": card_id, "title": title, "details": details}
            for column in board.get("columns", []):
                if column.get("id") == column_id:
                    column.setdefault("cardIds", []).append(card_id)
                    break
        elif update.get("type") == "delete-card":
            card_id = update.get("cardId")
            if not isinstance(card_id, str):
                raise HTTPException(status_code=400, detail="Invalid delete-card update")
            board.setdefault("cards", {}).pop(card_id, None)
            for column in board.get("columns", []):
                column["cardIds"] = [item for item in column.get("cardIds", []) if item != card_id]
        elif update.get("type") == "move-card":
            card_id = update.get("cardId")
            from_column_id = update.get("fromColumnId")
            to_column_id = update.get("toColumnId")
            if not isinstance(card_id, str) or not isinstance(from_column_id, str) or not isinstance(to_column_id, str):
                raise HTTPException(status_code=400, detail="Invalid move-card update")
            source_column = next((column for column in board.get("columns", []) if column.get("id") == from_column_id), None)
            target_column = next((column for column in board.get("columns", []) if column.get("id") == to_column_id), None)
            if not source_column or not target_column:
                raise HTTPException(status_code=400, detail="Invalid move-card update")
            source_column["cardIds"] = [item for item in source_column.get("cardIds", []) if item != card_id]
            target_column.setdefault("cardIds", []).append(card_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported update type")

    return {"message": message, "board": board}


@app.get("/api/boards/{user_id}")
def get_board(user_id: str) -> dict[str, Any]:
    return load_board(user_id)


@app.put("/api/boards/{user_id}")
def put_board(user_id: str, board: dict[str, Any]) -> dict[str, Any]:
    save_board(user_id, board)
    return board


@app.post("/api/boards/{user_id}/cards")
def create_card(user_id: str, payload: CardPayload) -> dict[str, Any]:
    board = load_board(user_id)
    card_id = f"card-{len(board['cards']) + 1}"
    board["cards"][card_id] = {
        "id": card_id,
        "title": payload.title,
        "details": payload.details,
    }
    for column in board["columns"]:
        if column["id"] == payload.columnId:
            column["cardIds"].append(card_id)
            break
    save_board(user_id, board)
    return board


@app.patch("/api/boards/{user_id}/columns/{column_id}")
def rename_column(user_id: str, column_id: str, payload: ColumnUpdatePayload) -> dict[str, Any]:
    board = load_board(user_id)
    for column in board["columns"]:
        if column["id"] == column_id:
            column["title"] = payload.title
            save_board(user_id, board)
            return board

    raise HTTPException(status_code=404, detail="Column not found")


@app.delete("/api/boards/{user_id}/cards/{card_id}")
def delete_card(user_id: str, card_id: str, columnId: str) -> dict[str, Any]:
    board = load_board(user_id)
    if card_id not in board["cards"]:
        raise HTTPException(status_code=404, detail="Card not found")

    for column in board["columns"]:
        if column["id"] == columnId:
            column["cardIds"] = [item for item in column["cardIds"] if item != card_id]
            break

    board["cards"].pop(card_id, None)
    save_board(user_id, board)
    return board


@app.post("/api/boards/{user_id}/move")
def move_card(user_id: str, payload: MovePayload) -> dict[str, Any]:
    board = load_board(user_id)
    source_column = next((column for column in board["columns"] if column["id"] == payload.fromColumnId), None)
    target_column = next((column for column in board["columns"] if column["id"] == payload.toColumnId), None)

    if not source_column or not target_column or payload.cardId not in board["cards"]:
        raise HTTPException(status_code=404, detail="Board update not found")

    source_column["cardIds"] = [card_id for card_id in source_column["cardIds"] if card_id != payload.cardId]
    target_column["cardIds"].append(payload.cardId)
    save_board(user_id, board)
    return board


if FRONTEND_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="frontend")
else:
    @app.get("/", response_class=HTMLResponse)
    def root() -> str:
        return """
        <html>
          <head>
            <title>Project Management MVP</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 2rem; }
              code { background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 4px; }
            </style>
          </head>
          <body>
            <h1>Hello world</h1>
            <p>The lightweight scaffolding is running.</p>
            <p>The frontend build has not been generated yet.</p>
            <p>Try <code>/api/health</code> for the API response.</p>
          </body>
        </html>
        """
