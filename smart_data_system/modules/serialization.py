"""
modules/serialization.py
------------------------
Handles JSON-based data persistence for processed results.

Concepts covered:
  - json module (dumps, loads, dump, load)
  - os module   (path operations, makedirs)
  - datetime module (timestamps)
  - Data Serialization pattern
"""

import json
import os
import datetime
from utils.decorators import log_call, timer

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DATASETS_FILE = os.path.join(DATA_DIR, "datasets.json")


def _ensure_dir():
    """Create the data directory if it doesn't exist (os module)."""
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_store() -> list:
    """Load the JSON store; return empty list if file doesn't exist."""
    _ensure_dir()
    if not os.path.exists(DATASETS_FILE):
        return []
    with open(DATASETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(records: list) -> None:
    """Persist the records list to the JSON store."""
    _ensure_dir()
    with open(DATASETS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)


@log_call
@timer
def save_result(name: str, stats: dict, chart_paths: list, user_info: dict) -> str:
    """
    Serialize a processing result and append it to datasets.json.

    Concept covered: JSON serialization – converts Python objects to JSON
    strings for persistent storage.

    Returns the unique record ID.
    """
    records = _load_store()

    record_id = f"rec_{len(records)+1:04d}"
    record = {
        "id": record_id,
        "name": name,
        "saved_at": datetime.datetime.now().isoformat(),
        "user": {k: v for k, v in user_info.items() if k != "password"},
        "statistics": stats,
        "chart_paths": chart_paths,
    }

    records.append(record)
    _save_store(records)
    return record_id


@log_call
def load_all_results() -> list:
    """Return all stored processing results."""
    return _load_store()


@log_call
def load_result_by_id(record_id: str) -> dict | None:
    """Return a single result by ID, or None if not found."""
    records = _load_store()
    return next((r for r in records if r["id"] == record_id), None)


@log_call
def delete_result(record_id: str) -> bool:
    """Delete a record by ID. Returns True if deleted."""
    records = _load_store()
    updated = [r for r in records if r["id"] != record_id]
    if len(updated) == len(records):
        return False
    _save_store(updated)
    return True


def export_to_json_string(data: dict) -> str:
    """Utility: serialize any dict to a pretty-printed JSON string."""
    return json.dumps(data, indent=2, default=str)
