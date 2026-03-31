"""Status bar — shows current agent, routing mode, and loading state."""

from __future__ import annotations

from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """

    agent_name: reactive[str] = reactive("none")
    agent_color: reactive[str] = reactive("#888888")
    route_mode: reactive[str] = reactive("auto")
    model_name: reactive[str] = reactive("")
    loading_text: reactive[str] = reactive("")

    def render(self) -> Text:
        result = Text()
        result.append(" nanocode ", style="bold")
        result.append(" │ ", style="dim")

        # Agent badge
        mode_icon = "⚡" if self.route_mode == "auto" else "📌"
        result.append(f" {self.agent_name} ", style=f"bold {self.agent_color}")
        result.append(f" {mode_icon}{self.route_mode} ", style="dim")

        # Model name
        if self.model_name:
            result.append(" │ ", style="dim")
            result.append(self.model_name, style="dim")

        # Loading text
        if self.loading_text:
            result.append(" │ ", style="dim")
            result.append(self.loading_text, style="dim italic")

        return result

    def set_agent(self, name: str, color: str, mode: str, model: str = "") -> None:
        self.agent_name = name
        self.agent_color = color
        self.route_mode = mode
        self.model_name = model
