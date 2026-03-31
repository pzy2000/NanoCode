"""Persistent conversation history — save, load, list, resume."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


def generate_session_id() -> str:
    return uuid.uuid4().hex[:12]


def format_session_list(sessions: list[dict]) -> str:
    if not sessions:
        return "No saved sessions found."
    lines = ["**Saved sessions** (newest first)\n"]
    for i, s in enumerate(sessions, 1):
        ts = s.get("timestamp", "")[:16].replace("T", " ")
        preview = s.get("preview", "")[:60]
        count = s.get("message_count", 0)
        cwd = s.get("cwd", "")
        lines.append(f"`{i}.` **{preview}**")
        lines.append(f"   {ts} · {count} messages · `{cwd}`")
        lines.append(f"   id: `{s['session_id']}`\n")
    lines.append("Use `/resume <n>` to restore a session.")
    return "\n".join(lines)


class HistoryManager:
    def __init__(self, base_dir: Path | str | None = None):
        if base_dir is None:
            base_dir = Path.home() / ".nanocode" / "history"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def save(self, session_id: str, messages: list[dict], cwd: str) -> None:
        preview = next(
            (m["content"][:80] for m in messages if m.get("role") == "user"),
            "(empty)",
        )
        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "cwd": cwd,
            "message_count": len(messages),
            "preview": preview,
            "messages": messages,
        }
        self._path(session_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

    def load(self, session_id: str) -> dict | None:
        p = self._path(session_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:
            return None

    def list_sessions(self) -> list[dict]:
        sessions = []
        for p in self.base_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text())
                sessions.append(
                    {
                        "session_id": data["session_id"],
                        "timestamp": data.get("timestamp", ""),
                        "cwd": data.get("cwd", ""),
                        "preview": data.get("preview", ""),
                        "message_count": data.get("message_count", 0),
                    }
                )
            except Exception:
                continue
        return sorted(sessions, key=lambda s: s["timestamp"], reverse=True)

    def delete(self, session_id: str) -> None:
        p = self._path(session_id)
        if p.exists():
            p.unlink()
