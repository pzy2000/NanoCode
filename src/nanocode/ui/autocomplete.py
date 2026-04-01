"""Slash command autocomplete for the TUI input."""

from __future__ import annotations

from dataclasses import dataclass

_PRESET_MODELS: list[str] = [
    "gpt-4o", "gpt-4o-mini", "gpt-4.5-preview",
    "MiniMax/MiniMax-M2.5", "qwen3.5-plus",
    "claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5",
]


@dataclass
class CompletionItem:
    value: str
    description: str


# Static command definitions: command -> (description, sub-completions)
_COMMANDS: dict[str, tuple[str, list[CompletionItem]]] = {
    "/agent": (
        "Switch agent or routing mode",
        [
            CompletionItem("/agent auto", "Enable auto-routing"),
            CompletionItem("/agent claude", "Lock to Claude Code"),
            CompletionItem("/agent codex", "Lock to Codex"),
            CompletionItem("/agent opencode", "Lock to OpenCode"),
        ],
    ),
    "/model": (
        "List or switch model",
        [
            CompletionItem(f"/model {m}", f"Switch to {m}")
            for m in _PRESET_MODELS
        ],
    ),
    "/resume": ("Restore a saved session", []),
    "/clear": ("Clear conversation history", []),
    "/help": ("Show help", []),
    "/?": ("Show help", []),
    "/exit": ("Exit nanocode", []),
    "/quit": ("Exit nanocode", []),
}


class SlashCompleter:
    """Tab-completion engine for slash commands and their arguments."""

    def __init__(self) -> None:
        self._results: list[CompletionItem] = []
        self._index: int = 0

    def complete(self, text: str) -> list[CompletionItem]:
        """Compute completions for *text*. Returns the list and resets cycle."""
        self._results = []
        self._index = 0

        if not text or not text.startswith("/"):
            return []

        # Argument completion: "/cmd <partial>"
        for cmd, (desc, subs) in _COMMANDS.items():
            prefix = cmd + " "
            if text.startswith(prefix):
                arg = text[len(prefix):]
                self._results = [s for s in subs if s.value[len(prefix):].startswith(arg)]
                return self._results

        # Command completion: "/partial"
        self._results = [
            CompletionItem(cmd, desc)
            for cmd, (desc, _) in _COMMANDS.items()
            if cmd.startswith(text)
        ]
        return self._results

    def next(self) -> CompletionItem | None:
        """Cycle to the next completion item."""
        if not self._results:
            return None
        item = self._results[self._index]
        self._index = (self._index + 1) % len(self._results)
        return item

    def reset(self) -> None:
        self._results = []
        self._index = 0
