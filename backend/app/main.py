import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
import json
import re

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_BUILD_DIR = ROOT_DIR / "frontend" / "out"
DB_PATH = Path(os.getenv("PROJECT_MGMT_DB_PATH", ROOT_DIR / "backend" / "app" / "project_management.db"))

load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")

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
    def apply_local_fallback(prompt_text: str, current_board: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        prompt_lower = prompt_text.lower()
        columns = current_board.get("columns", [])
        cards = current_board.get("cards", {})

        def normalize_text(value: str) -> str:
            return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

        def find_column_by_name(name: str) -> dict[str, Any] | None:
            target = normalize_text(name)
            for col in columns:
                title = normalize_text(str(col.get("title", "")))
                if title == target or target in title or title in target:
                    return col
            return None

        def find_card_id_by_title(title: str) -> str | None:
            target = title.strip().lower()
            for card_id, card in cards.items():
                if str(card.get("title", "")).strip().lower() == target:
                    return card_id
            return None

        if "rename card" in prompt_lower and " to " in prompt_lower:
            after_rename = prompt_text.lower().split("rename card", 1)[1]
            split_index = after_rename.find(" to ")
            source_title = prompt_text[len(prompt_text) - len(after_rename): len(prompt_text) - len(after_rename) + split_index].strip(" .,")
            new_title = prompt_text[len(prompt_text) - len(after_rename) + split_index + 4 :].strip(" .,")
            card_id = find_card_id_by_title(source_title)
            if card_id and new_title:
                current_board.setdefault("cards", {}).setdefault(card_id, {})["title"] = new_title
                return f"Renamed card '{source_title}' to '{new_title}'.", current_board
            return "I could not find that card title to rename.", current_board

        rename_patterns = [
            r"rename\s+(?:the\s+)?column\s+(.+?)\s+to\s+(.+)",
            r"rename\s+(.+?)\s+column\s+to\s+(.+)",
            r"rename\s+(.+?)\s+to\s+(.+)",
        ]
        for pattern in rename_patterns:
            match = re.search(pattern, prompt_text, flags=re.IGNORECASE)
            if not match:
                continue
            old_title = match.group(1).strip(" .,")
            new_title = match.group(2).strip(" .,")
            if old_title.lower().startswith("card "):
                break
            target_column = find_column_by_name(old_title)
            if target_column and new_title:
                target_column["title"] = new_title
                return f"Renamed column '{old_title}' to '{new_title}'.", current_board
            return "I could not find that column title to rename.", current_board

        if "add card" in prompt_lower and " to " in prompt_lower:
            after_add = prompt_text.lower().split("add card", 1)[1]
            split_index = after_add.rfind(" to ")
            card_title = prompt_text[len(prompt_text) - len(after_add): len(prompt_text) - len(after_add) + split_index].strip(" .,")
            column_title = prompt_text[len(prompt_text) - len(after_add) + split_index + 4 :].strip(" .,")
            target_column = find_column_by_name(column_title)
            if target_column and card_title:
                card_id = f"card-{len(cards) + 1}"
                current_board.setdefault("cards", {})[card_id] = {
                    "id": card_id,
                    "title": card_title,
                    "details": "Added by local fallback assistant.",
                }
                target_column.setdefault("cardIds", []).append(card_id)
                return f"Added card '{card_title}' to '{target_column.get('title', column_title)}'.", current_board
            return "I could not add that card because the target column was not found.", current_board

        if "move card" in prompt_lower and " to " in prompt_lower:
            after_move = prompt_text.lower().split("move card", 1)[1]
            split_index = after_move.rfind(" to ")
            card_title = prompt_text[len(prompt_text) - len(after_move): len(prompt_text) - len(after_move) + split_index].strip(" .,")
            column_title = prompt_text[len(prompt_text) - len(after_move) + split_index + 4 :].strip(" .,")
            card_id = find_card_id_by_title(card_title)
            target_column = find_column_by_name(column_title)
            if card_id and target_column:
                for col in columns:
                    col["cardIds"] = [item for item in col.get("cardIds", []) if item != card_id]
                target_column.setdefault("cardIds", []).append(card_id)
                return f"Moved card '{card_title}' to '{target_column.get('title', column_title)}'.", current_board
            return "I could not move that card because the card or destination column was not found.", current_board

        return (
            "The assistant is running in local fallback mode. Try: rename column Backlog to Ready, add card Draft launch checklist to Review, move card QA micro-interactions to Done, or rename card QA micro-interactions to QA interactions.",
            current_board,
        )

    api_key = os.getenv("OPENROUTER_API_KEY")
    board = payload.board

    if api_key:
        try:
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

            parsed = None
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                except Exception:
                    parsed = None

            if isinstance(parsed, dict):
                message = parsed.get("message", "")
                updates = parsed.get("updates", [])
                if isinstance(updates, list):
                    for update in updates:
                        if not isinstance(update, dict):
                            continue
                        update_type = str(update.get("type", "")).replace("_", "-").lower()

                        if update_type == "rename-column":
                            column_id = update.get("columnId") or update.get("column_id") or update.get("id")
                            old_title = update.get("columnTitle") or update.get("oldTitle") or update.get("from")
                            title = update.get("title") or update.get("newTitle") or update.get("name") or update.get("to")
                            if isinstance(title, str):
                                updated = False
                                if isinstance(column_id, str):
                                    for column in board.get("columns", []):
                                        if column.get("id") == column_id:
                                            column["title"] = title
                                            updated = True
                                            break
                                if not updated and isinstance(old_title, str):
                                    for column in board.get("columns", []):
                                        if str(column.get("title", "")).strip().lower() == old_title.strip().lower():
                                            column["title"] = title
                                            break
                        elif update_type == "rename-card":
                            card_id = update.get("cardId")
                            title = update.get("title") or update.get("newTitle") or update.get("name")
                            if isinstance(card_id, str) and isinstance(title, str) and card_id in board.get("cards", {}):
                                board["cards"][card_id]["title"] = title
                        elif update_type == "add-card":
                            column_id = update.get("columnId")
                            title = update.get("title")
                            details = update.get("details", "")
                            if isinstance(column_id, str) and isinstance(title, str):
                                card_id = f"card-{len(board.get('cards', {})) + 1}"
                                board.setdefault("cards", {})[card_id] = {"id": card_id, "title": title, "details": details}
                                for column in board.get("columns", []):
                                    if column.get("id") == column_id:
                                        column.setdefault("cardIds", []).append(card_id)
                                        break
                        elif update_type == "delete-card":
                            card_id = update.get("cardId")
                            if isinstance(card_id, str):
                                board.setdefault("cards", {}).pop(card_id, None)
                                for column in board.get("columns", []):
                                    column["cardIds"] = [item for item in column.get("cardIds", []) if item != card_id]
                        elif update_type == "move-card":
                            card_id = update.get("cardId")
                            from_column_id = update.get("fromColumnId")
                            to_column_id = update.get("toColumnId")
                            if isinstance(card_id, str) and isinstance(from_column_id, str) and isinstance(to_column_id, str):
                                source_column = next((column for column in board.get("columns", []) if column.get("id") == from_column_id), None)
                                target_column = next((column for column in board.get("columns", []) if column.get("id") == to_column_id), None)
                                if source_column and target_column:
                                    source_column["cardIds"] = [item for item in source_column.get("cardIds", []) if item != card_id]
                                    target_column.setdefault("cardIds", []).append(card_id)

                if isinstance(message, str) and message.strip():
                    return {"message": message, "board": board}

            if isinstance(content, str) and content.strip():
                prompt_lower = payload.prompt.lower()
                if any(keyword in prompt_lower for keyword in ["rename", "move", "add", "delete"]):
                    fallback_message, updated_board = apply_local_fallback(payload.prompt, board)
                    if not fallback_message.startswith("The assistant is running in local fallback mode"):
                        return {
                            "message": f"{content.strip()}\n{fallback_message}",
                            "board": updated_board,
                        }
                return {"message": content.strip(), "board": board}
        except Exception:
            pass

    message, updated_board = apply_local_fallback(payload.prompt, board)
    return {
        "message": message,
        "board": updated_board,
    }


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
