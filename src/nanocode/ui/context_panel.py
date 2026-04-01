"""Context panel — displays token usage, context %, and cost statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static

from nanocode.pricing import calc_cost, context_pct


@dataclass
class ContextStats:
    """Accumulated usage statistics for a session."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    last_input_tokens: int = 0

    def add(self, input_tokens: int, output_tokens: int, cost: float) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.last_input_tokens = input_tokens

    def reset(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.last_input_tokens = 0

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "last_input_tokens": self.last_input_tokens,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ContextStats:
        return cls(
            total_input_tokens=d.get("total_input_tokens", 0),
            total_output_tokens=d.get("total_output_tokens", 0),
            total_cost=d.get("total_cost", 0.0),
            last_input_tokens=d.get("last_input_tokens", 0),
        )


class ContextPanel(Widget):
    """Sidebar panel showing Context / tokens / % used / $ spent."""

    DEFAULT_CSS = """
    ContextPanel {
        height: auto;
        border: solid $primary-background;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stats = ContextStats()
        self._model: str = ""

    def compose(self) -> ComposeResult:
        yield Static(self.render_stats(), id="context-text")

    def on_mount(self) -> None:
        self.border_title = "Context"

    def render_stats(self) -> str:
        """Return a plain-text representation of current stats (used in tests too)."""
        s = self._stats
        lines = ["Context"]

        # Token count (last request = current context size)
        lines.append(f"{s.last_input_tokens:,} tokens")

        # Context % used
        pct = context_pct(self._model, s.last_input_tokens) if self._model else None
        if pct is not None:
            pct_str = f"{pct:.0f}% used"
            if pct >= 80:
                pct_str += " !"
            lines.append(pct_str)
        else:
            lines.append("N/A used")

        # Cumulative cost
        if s.total_cost > 0 or self._model:
            cost = s.total_cost
            if cost == 0.0 and not self._model:
                lines.append("N/A spent")
            else:
                # Check if model is known for cost display
                test_cost = calc_cost(self._model, 0, 0)
                if test_cost is None:
                    lines.append("N/A spent")
                else:
                    lines.append(f"${cost:.2f} spent")
        else:
            lines.append("$0.00 spent")

        return "\n".join(lines)

    def update_usage(self, input_tokens: int, output_tokens: int, model: str) -> None:
        """Accumulate usage from one LLM call and refresh display."""
        self._model = model
        cost = calc_cost(model, input_tokens, output_tokens)
        self._stats.add(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost if cost is not None else 0.0,
        )
        self._refresh_display()

    def get_stats(self) -> ContextStats:
        return self._stats

    def load_stats(self, stats: ContextStats) -> None:
        """Restore stats from a saved session."""
        self._stats = stats
        self._refresh_display()

    def _refresh_display(self) -> None:
        try:
            self.query_one("#context-text", Static).update(self.render_stats())
        except Exception:
            pass
