"""Greek mythology themed loading indicator."""

from __future__ import annotations

import random
from time import time

from rich.style import Style
from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive

THINKING_PHRASES = [
    "Consulting the Oracle at Delphi...",
    "Weaving code with Athena...",
    "Forging in Hephaestus' workshop...",
    "Navigating the labyrinth...",
    "Stealing fire from Olympus...",
    "Summoning the Muses...",
    "Charting course with Odysseus...",
    "Unraveling Ariadne's thread...",
    "Ascending Mount Parnassus...",
    "Deciphering the Sibylline Books...",
    "Crossing the River Styx...",
    "Taming Pegasus...",
]

TOOL_PHRASES = [
    "Hermes is delivering...",
    "Apollo examines the code...",
    "Hephaestus hammers the changes...",
    "Athena reviews the strategy...",
    "Prometheus lights the way...",
    "Daedalus engineers a solution...",
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

    def start(self, mode: str = "thinking") -> None:
        phrases = THINKING_PHRASES if mode == "thinking" else TOOL_PHRASES
        self.phrase = random.choice(phrases)
        self.is_active = True
        self._start_time = time()
        self.auto_refresh = 1 / 12

    def stop(self) -> None:
        self.is_active = False
        self.auto_refresh = None

    def render(self) -> Text:
        if not self.is_active:
            return Text("")

        elapsed = time() - self._start_time
        speed = 0.8
        dot = "\u25cf"  # ●

        # Animated gradient dots
        dots_parts = []
        for i in range(4):
            blend = (elapsed * speed - i / 6) % 1
            brightness = int(80 + 175 * ((1 - blend) ** 2))
            color = f"rgb({brightness},{brightness},{255})"
            dots_parts.append((f"{dot} ", Style(color=color)))

        result = Text.assemble(*dots_parts)
        result.append(self.phrase, style="dim italic")
        return result
