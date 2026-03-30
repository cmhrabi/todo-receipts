import json
from pathlib import Path

STATE_FILE = Path(".last_seen.json")
MAX_PROCESSED_IDS = 100


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"processed_ids": set(), "last_created_time": None}
    with STATE_FILE.open() as f:
        data = json.load(f)
    return {
        "processed_ids": set(data.get("processed_ids", [])),
        "last_created_time": data.get("last_created_time"),
    }


def save_state(state: dict) -> None:
    ids_list = list(state["processed_ids"])[-MAX_PROCESSED_IDS:]
    with STATE_FILE.open("w") as f:
        json.dump({
            "processed_ids": ids_list,
            "last_created_time": state["last_created_time"],
        }, f)


def is_processed(page_id: str, state: dict) -> bool:
    return page_id in state["processed_ids"]


def mark_processed(page_id: str, state: dict) -> dict:
    state["processed_ids"].add(page_id)
    return state


def update_cursor(state: dict, created_time: str) -> dict:
    if state["last_created_time"] is None or created_time > state["last_created_time"]:
        state["last_created_time"] = created_time
    return state
