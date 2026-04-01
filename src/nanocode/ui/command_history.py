"""Command history — persistent cross-session input history with navigation."""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_PATH = Path.home() / ".nanocode" / "command_history.json"
_DEFAULT_MAX = 500


class CommandHistory:
    """Stores and navigates a persistent list of past commands."""

    def __init__(self, path: Path | None = None, max_size: int = _DEFAULT_MAX) -> None:
        self._path = Path(path) if path else _DEFAULT_PATH
        self._max_size = max_size
        self._pos: int = -1  # -1 = not navigating
        self.entries: list[str] = []
        self._load()

    # === Mutation ===

    def add(self, text: str) -> None:
        """Append a command, skipping blanks and consecutive duplicates."""
        text = text.strip()
        if not text:
            return
        if self.entries and self.entries[-1] == text:
            self._pos = -1
            return
        self.entries.append(text)
        if len(self.entries) > self._max_size:
            self.entries = self.entries[-self._max_size :]
        self._pos = -1

    # === Navigation ===

    def navigate_up(self) -> str | None:
        """Move backward (older). Returns the entry or None if empty."""
        if not self.entries:
            return None
        if self._pos == -1:
            self._pos = len(self.entries) - 1
        else:
            self._pos = max(0, self._pos - 1)
        return self.entries[self._pos]

    def navigate_down(self) -> str | None:
        """Move forward (newer). Returns the entry or None when past the end."""
        if not self.entries or self._pos == -1:
            return None
        self._pos += 1
        if self._pos >= len(self.entries):
            self._pos = -1
            return None
        return self.entries[self._pos]

    def reset(self) -> None:
        """Reset navigation cursor without clearing entries."""
        self._pos = -1

    # === Persistence ===

    def save(self) -> None:
        """Persist entries to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2))

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text())
            if isinstance(data, list):
                self.entries = [str(e) for e in data]
        except Exception:
            self.entries = []
