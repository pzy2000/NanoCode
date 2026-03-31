"""Main Textual TUI application."""

from __future__ import annotations

import os

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Input

from nanocode.engine import (
    Engine,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
    StatusEvent,
    create_backend,
)
from nanocode.router import Router
from nanocode.ui.chat_view import ChatView
from nanocode.ui.status_bar import StatusBar
from nanocode.ui.terminal_view import TerminalView

HELP_TEXT = """## nanocode — Available Commands

### Agent Control
| Command | Description |
|---------|-------------|
| `/agent auto` | Enable auto-routing — LLM picks the best agent per request |
| `/agent claude` | Lock to **Claude Code** — careful reasoning, reads before editing, asks before writing |
| `/agent codex` | Lock to **Codex** — direct code generation, shell-only, auto-approves all tools |
| `/agent opencode` | Lock to **OpenCode** — complex refactoring, full tool access, fully autonomous |
| `/agent` | Show current mode and active agent |

### Session
| Command | Description |
|---------|-------------|
| `/clear` | Clear conversation history and reset message context |
| `/help` or `/?` | Show this help message |
| `/exit` or `/quit` | Exit nanocode |
| `Ctrl+C` | Exit nanocode |

### Agent Styles at a Glance
```
claude    — tools: all 6  | approval: prompt | best for: review, debug, explain
codex     — tools: shell  | approval: auto   | best for: generate, build, deploy
opencode  — tools: all 6  | approval: none   | best for: refactor, scaffold
```

### Auto-Routing
When in `auto` mode, nanocode sends a lightweight classification call to the LLM
before each request to pick the most suitable agent. The status bar shows which
agent was selected and whether routing is automatic (⚡auto) or pinned (📌).

### Tips
- Type any message to start coding — no command needed
- Switch agents mid-conversation without losing history
- The terminal panel (right) shows all tool calls and their output
"""


class NanoCodeApp(App):
    TITLE = "nanocode"
    CSS = """
    Screen {
        layout: vertical;
    }
    #main-panels {
        layout: horizontal;
        height: 1fr;
    }
    #left-panel {
        width: 1fr;
    }
    #right-panel {
        width: 1fr;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, provider: str = "openai", **kwargs):
        super().__init__(**kwargs)
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY", ""
        )
        base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get(
            "ANTHROPIC_BASE_URL"
        )
        model = os.environ.get("NANOCODE_MODEL", "gpt-4o")

        if not provider:
            provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"

        backend = create_backend(
            provider, api_key=api_key, base_url=base_url, model=model
        )
        self.engine = Engine(backend)
        self.router = Router(self.engine, cwd=os.getcwd())

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status-bar")
        with Horizontal(id="main-panels"):
            with Vertical(id="left-panel"):
                yield ChatView(id="chat-view")
            with Vertical(id="right-panel"):
                yield TerminalView(id="terminal-view")
        yield Footer()

    def on_mount(self) -> None:
        status = self.query_one("#status-bar", StatusBar)
        status.set_agent("none", "#888888", "auto")
        # Show welcome message
        chat = self.query_one("#chat-view", ChatView)
        chat.add_message("system", self._welcome_text())
        self.query_one("#chat-input", Input).focus()

    def _welcome_text(self) -> str:
        model = os.environ.get("NANOCODE_MODEL", "gpt-4o")
        cwd = os.getcwd()
        provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"
        return f"""## ⚡ Welcome to nanocode

A micro coding agent that auto-routes between **Claude Code**, **Codex**, and **OpenCode** styles.

| | |
|---|---|
| **Model** | `{model}` |
| **Provider** | `{provider}` |
| **Working directory** | `{cwd}` |
| **Routing mode** | `auto` |

### Quick Start
- Just type your coding request — nanocode will pick the right agent automatically
- `/agent claude` · `/agent codex` · `/agent opencode` to lock a specific style
- `/agent auto` to re-enable auto-routing
- `/help` for the full command reference
- `Ctrl+C` to exit

*Consulting the Oracle at Delphi...* 🏛️
"""

    @on(Input.Submitted, "#chat-input")
    def on_chat_submit(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""

        # Handle commands
        if text.startswith("/"):
            if text in ("/exit", "/quit"):
                self.exit()
                return
            if text == "/clear":
                self.query_one("#chat-view", ChatView).clear_messages()
                self.engine.messages.clear()
                return
            if text in ("/help", "/?"):
                self.query_one("#chat-view", ChatView).add_message("system", HELP_TEXT)
                return
            agent_result = self.router.handle_command(text)
            if agent_result is not None:
                chat = self.query_one("#chat-view", ChatView)
                chat.add_message("system", agent_result)
                self._update_status_bar()
                return
            # Unknown command
            self.query_one("#chat-view", ChatView).add_message(
                "system",
                f"Unknown command: `{text}`\nType `/help` to see all available commands.",
            )

        # Normal message
        chat = self.query_one("#chat-view", ChatView)
        chat.add_message("user", text)
        self._run_agent(text)

    @work(thread=False)
    async def _run_agent(self, user_input: str) -> None:
        chat = self.query_one("#chat-view", ChatView)
        terminal = self.query_one("#terminal-view", TerminalView)
        status = self.query_one("#status-bar", StatusBar)

        # Route to agent
        config = await self.router.resolve(user_input)
        self._update_status_bar()

        chat.start_loading("thinking")
        assistant_text = ""
        current_msg = None

        try:
            async for event in self.engine.submit(user_input):
                if isinstance(event, StatusEvent):
                    if event.status == "thinking":
                        chat.start_loading("thinking")
                    elif event.status == "done":
                        chat.stop_loading()

                elif isinstance(event, TextEvent):
                    if current_msg is None:
                        chat.stop_loading()
                        current_msg = chat.add_message("assistant", "")
                    assistant_text += event.text
                    current_msg.update_content(
                        assistant_text
                    )  # direct ref, no DOM search

                elif isinstance(event, ToolCallEvent):
                    chat.start_loading("tool")
                    terminal.log_tool_call(event.name, event.args)
                    status.loading_text = f"▶ {event.name}"

                elif isinstance(event, ToolResultEvent):
                    terminal.log_tool_result(
                        event.name, event.result.content, event.result.is_error
                    )
                    status.loading_text = ""
                    # Reset for next text chunk
                    assistant_text = ""
                    current_msg = None

        except Exception as e:
            chat.stop_loading()
            chat.add_message("system", f"Error: {e}")
        finally:
            chat.stop_loading()
            status.loading_text = ""

    def _update_status_bar(self) -> None:
        status = self.query_one("#status-bar", StatusBar)
        agent = self.router.current_agent
        if agent:
            status.set_agent(agent.display_name, agent.color, self.router.mode)
        else:
            status.set_agent("none", "#888888", self.router.mode)
