"""Funny loading indicator with spinner animation."""

from __future__ import annotations

import random
from time import time

from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive
from textual.timer import Timer

SPINNER_FRAMES = ["|", "/", "-", "\\"]

THINKING_PHRASES = [
    "doing your homework...",
    "cooking your dinner...",
    "dating a girl for you...",
    "walking your dog...",
    "filing your taxes...",
    "writing your resignation letter...",
    "pretending to understand the requirements...",
    "blaming it on the compiler...",
    "googling Stack Overflow...",
    "making stuff up confidently...",
    "reading the docs (just kidding)...",
    "asking ChatGPT (ironic, right)...",
]

TOOL_PHRASES = [
    "touching your files...",
    "running commands you didn't ask for...",
    "deleting system32 (just kidding)...",
    "making it worse before better...",
    "committing crimes against your codebase...",
]


class LoadingIndicator(Widget):
    DEFAULT_CSS = """
    LoadingIndicator {
        height: 1;
        padding: 0 1;
    }
    """

    phrase: reactive[str] = reactive("")
    is_active: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._start_time = time()
        self._timer: Timer | None = None
        self._pending_mode: str | None = None

    def watch_is_active(self, value: bool) -> None:
        self.display = value
        self.visible = value
        self.refresh()

    def on_mount(self) -> None:
        self.display = False
        self._start_pending_timer()

    def _start_pending_timer(self) -> None:
        if self._pending_mode is not None and self._timer is None:
            self._timer = self.set_interval(1 / 12, self.refresh)
            self._pending_mode = None

    def start(self, mode: str = "thinking") -> None:
        phrases = THINKING_PHRASES if mode == "thinking" else TOOL_PHRASES
        self.phrase = random.choice(phrases)
        self.is_active = True
        self._start_time = time()
        if self._timer is None:
            try:
                self._timer = self.set_interval(1 / 12, self.refresh)
            except Exception:
                self._pending_mode = mode

    def stop(self) -> None:
        self.is_active = False
        self._pending_mode = None
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def render(self) -> Text:
        if not self.is_active:
            return Text("")

        elapsed = time() - self._start_time
        frame = SPINNER_FRAMES[int(elapsed * 10) % len(SPINNER_FRAMES)]

        result = Text()
        result.append(f"{frame} ", style="bold")
        result.append(self.phrase, style="dim italic")
        return result
