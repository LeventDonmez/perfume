from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {
            "seen": {},
            "next_check_at": None,
            "last_check_at": None,
            "bootstrapped": False,
        }
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        loaded = json.loads(self.path.read_text(encoding="utf-8"))
        self.data.update(loaded)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @property
    def seen(self) -> dict[str, dict[str, Any]]:
        return self.data.setdefault("seen", {})

    @property
    def bootstrapped(self) -> bool:
        return bool(self.data.get("bootstrapped"))

    @bootstrapped.setter
    def bootstrapped(self, value: bool) -> None:
        self.data["bootstrapped"] = value

    @property
    def next_check_at(self) -> datetime | None:
        return parse_iso(self.data.get("next_check_at"))

    @next_check_at.setter
    def next_check_at(self, value: datetime | None) -> None:
        self.data["next_check_at"] = value.isoformat() if value else None

    @property
    def last_check_at(self) -> datetime | None:
        return parse_iso(self.data.get("last_check_at"))

    @last_check_at.setter
    def last_check_at(self, value: datetime | None) -> None:
        self.data["last_check_at"] = value.isoformat() if value else None
