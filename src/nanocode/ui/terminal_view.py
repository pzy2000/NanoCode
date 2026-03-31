"""Terminal view — displays tool call output."""

from __future__ import annotations

from textual.widgets import RichLog


class TerminalView(RichLog):
    DEFAULT_CSS = """
    TerminalView {
        border: solid $primary-background;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    """

    def on_mount(self) -> None:
        self.border_title = "Terminal"

    def log_tool_call(self, name: str, args: dict) -> None:
        preview = ""
        if "command" in args:
            preview = args["command"][:80]
        elif "file_path" in args:
            preview = args["file_path"]
        elif "pattern" in args:
            preview = args["pattern"]
        self.write(f"[dim]▶ {name}:[/dim] {preview}")

    def log_tool_result(self, name: str, content: str, is_error: bool) -> None:
        style = "red" if is_error else "dim green"
        icon = "✗" if is_error else "✓"
        self.write(f"[{style}]{icon}[/{style}] {name}")
        # Show truncated output
        lines = content.strip().splitlines()
        for line in lines[:10]:
            self.write(f"  [dim]{line[:120]}[/dim]")
        if len(lines) > 10:
            self.write(f"  [dim]... ({len(lines) - 10} more lines)[/dim]")
