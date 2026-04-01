"""Chat view — message list + input area with history navigation and autocomplete."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.events import Key
from textual.widgets import Input, Markdown, Static
from textual.reactive import reactive
from textual.widget import Widget

from nanocode.ui.loading import LoadingIndicator
from nanocode.ui.command_history import CommandHistory
from nanocode.ui.autocomplete import SlashCompleter


class SmartInput(Input):
    """Input with ↑/↓ history navigation and Tab autocomplete."""

    def __init__(self, history: CommandHistory, completer: SlashCompleter, **kwargs):
        super().__init__(**kwargs)
        self._history = history
        self._completer = completer
        self._tab_active = False

    def on_key(self, event: Key) -> None:
        if event.key == "up":
            result = self._history.navigate_up()
            if result is not None:
                self.value = result
                self.cursor_position = len(result)
            event.prevent_default()
            event.stop()

        elif event.key == "down":
            result = self._history.navigate_down()
            self.value = result or ""
            if result:
                self.cursor_position = len(result)
            event.prevent_default()
            event.stop()

        elif event.key == "tab":
            if not self._tab_active:
                self._completer.complete(self.value)
                self._tab_active = True
            item = self._completer.next()
            if item:
                self.value = item.value
                self.cursor_position = len(item.value)
            event.prevent_default()
            event.stop()

        elif event.key == "escape":
            self._history.reset()
            self._completer.reset()
            self._tab_active = False

        else:
            # Any other key resets tab-cycle state
            self._tab_active = False

    def on_input_changed(self, event: Input.Changed) -> None:
        if not self._tab_active:
            self._completer.reset()
            # Notify parent to refresh hint
            try:
                parent = self.parent
                if parent is not None:
                    parent._update_hint(event.value)  # type: ignore[attr-defined]
            except Exception:
                pass


class MessageItem(Static):
    """A single chat message."""

    DEFAULT_CSS = """
    MessageItem { padding: 0 1; margin: 0 0 1 0; }
    MessageItem.user { color: $text; }
    MessageItem.assistant { color: $success; }
    MessageItem.system { color: $warning; }
    """

    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self._content = content

    def compose(self) -> ComposeResult:
        icon = {"user": "🧑", "assistant": "🤖", "system": "⚙️"}.get(self.role, "")
        yield Static(f"{icon} [{self.role}]", classes="role-label")
        yield Markdown(self._content)

    def on_mount(self) -> None:
        self.add_class(self.role)

    def update_content(self, content: str) -> None:
        self._content = content
        try:
            md = self.query_one(Markdown)
            md.update(content)
        except Exception:
            pass


class ChatView(Widget):
    """Chat panel with message list, smart input (history + autocomplete)."""

    DEFAULT_CSS = """
    ChatView {
        layout: vertical;
        border: solid $primary-background;
    }
    #message-scroll {
        height: 1fr;
        scrollbar-size: 1 1;
    }
    #completion-hint {
        dock: bottom;
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    #chat-input {
        dock: bottom;
        height: 3;
        margin: 0 0;
    }
    #loading {
        dock: bottom;
        height: 1;
    }
    """

    is_generating: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_history = CommandHistory()
        self._completer = SlashCompleter()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="message-scroll")
        yield LoadingIndicator(id="loading")
        yield Static("", id="completion-hint")
        yield SmartInput(
            self.command_history,
            self._completer,
            placeholder="Type a message... (Tab to complete, ↑↓ for history)",
            id="chat-input",
        )

    def on_mount(self) -> None:
        self.border_title = "Chat"
        # Hide hint initially
        self.query_one("#completion-hint", Static).display = False

    def _update_hint(self, text: str) -> None:
        """Update the inline completion hint as the user types."""
        try:
            hint = self.query_one("#completion-hint", Static)
            results = self._completer.complete(text)
            if results:
                first = results[0]
                hint.update(f"  {first.value}  — {first.description}")
                hint.display = True
            else:
                hint.update("")
                hint.display = False
        except Exception:
            pass

    def add_message(self, role: str, content: str) -> MessageItem:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        msg = MessageItem(role, content)
        scroll.mount(msg)
        scroll.scroll_end(animate=False)
        return msg

    def update_last_assistant(self, content: str) -> None:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        items = scroll.query(MessageItem)
        for item in reversed(list(items)):
            if item.role == "assistant":
                item.update_content(content)
                scroll.scroll_end(animate=False)
                return

    def start_loading(self, mode: str = "thinking") -> None:
        self.is_generating = True
        self.query_one("#loading", LoadingIndicator).start(mode)

    def stop_loading(self) -> None:
        self.is_generating = False
        self.query_one("#loading", LoadingIndicator).stop()

    def clear_messages(self) -> None:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        scroll.remove_children()
