"""Chat view — message list + input area."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, Markdown, Static
from textual.reactive import reactive
from textual.widget import Widget

from nanocode.ui.loading import LoadingIndicator


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
    """Chat panel with message list and input."""

    DEFAULT_CSS = """
    ChatView {
        layout: vertical;
        border: solid $primary-background;
    }
    #message-scroll {
        height: 1fr;
        scrollbar-size: 1 1;
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

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="message-scroll")
        yield LoadingIndicator(id="loading")
        yield Input(placeholder="Type a message... (/agent to switch)", id="chat-input")

    def on_mount(self) -> None:
        self.border_title = "Chat"

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
