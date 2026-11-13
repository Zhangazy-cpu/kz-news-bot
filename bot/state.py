import json
from datetime import datetime, timezone

from . import STATE_FILE


def load() -> list[dict]:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def add(entry: dict) -> None:
    items = load()
    entry = {"posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
    items.append(entry)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(items[-400:], ensure_ascii=False, indent=1), encoding="utf-8")
