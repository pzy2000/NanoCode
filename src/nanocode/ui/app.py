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
    UsageEvent,
    create_backend,
)
from nanocode.router import Router
from nanocode.history import HistoryManager, generate_session_id, format_session_list
from nanocode.ui.chat_view import ChatView
from nanocode.ui.status_bar import StatusBar
from nanocode.ui.terminal_view import TerminalView
from nanocode.ui.context_panel import ContextPanel, ContextStats

PRESET_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.5-preview",
        "MiniMax/MiniMax-M2.5",
        "qwen3.5-plus",
    ],
    "anthropic": [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
    ],
}

_COMPACT_THRESHOLD = 80.0  # auto-compact when context % >= this


def format_model_list(models: list[str], current: str) -> str:
    lines = ["**Available models** (current marked with ✓)\n"]
    for i, m in enumerate(models, 1):
        marker = " ✓" if m == current else ""
        lines.append(f"`{i}.` `{m}`{marker}")
    lines.append(f"\nUse `/model <n>` or `/model <name>` to switch.")
    return "\n".join(lines)


def handle_model_command(text: str, engine, provider: str) -> str | None:
    """Handle /model command. Returns message or None if not a /model command."""
    if not text.startswith("/model"):
        return None

    models = PRESET_MODELS.get(provider, PRESET_MODELS["openai"])
    current = engine.get_model()
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        return format_model_list(models, current)

    arg = parts[1].strip()

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(models):
            return f"Invalid model number `{arg}`. Valid range: 1–{len(models)}."
        model = models[idx]
        engine.set_model(model)
        return f"Switched to `{model}`"

    engine.set_model(arg)
    marker = " (preset)" if arg in models else " (custom)"
    return f"Switched to `{arg}`{marker}"


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
| `/resume` | List saved sessions (newest first) |
| `/resume <n>` | Restore session number `n` from the list |
| `/model` | List available models |
| `/model <n>` | Switch to preset model number `n` |
| `/model <name>` | Switch to any model by name (custom models supported) |
| `/compact` | Summarize conversation to reduce context usage |
| `/clear` | Clear conversation history and reset message context |
| `/help` or `/?` | Show this help message |
| `/exit` or `/quit` | Exit nanocode |
| `Ctrl+C` | Exit nanocode |

### Context Management
```
Context panel (top-right) shows:
  tokens   — input tokens in last request (= current context size)
  % used   — percentage of model's context window consumed
  $ spent  — cumulative cost for this session
```
When context reaches **80%**, nanocode auto-runs `/compact`.

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

### History
Conversations are automatically saved to `~/.nanocode/history/` after each turn.
Use `/resume` to list and restore previous sessions.

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
    #context-panel {
        height: auto;
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
        self._provider = provider
        self.history = HistoryManager()
        self.session_id = generate_session_id()

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status-bar")
        with Horizontal(id="main-panels"):
            with Vertical(id="left-panel"):
                yield ChatView(id="chat-view")
            with Vertical(id="right-panel"):
                yield ContextPanel(id="context-panel")
                yield TerminalView(id="terminal-view")
        yield Footer()

    def on_mount(self) -> None:
        status = self.query_one("#status-bar", StatusBar)
        status.set_agent("none", "#888888", "auto")
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
- `/compact` to summarize context when it gets large
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

        # Save to command history
        chat_view = self.query_one("#chat-view", ChatView)
        chat_view.command_history.add(text)
        chat_view.command_history.save()

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
            if text == "/compact":
                self._run_compact(auto=False)
                return
            if text == "/resume" or text.startswith("/resume "):
                self._handle_resume(text)
                return
            if text == "/model" or text.startswith("/model "):
                result = handle_model_command(text, self.engine, self._provider)
                self.query_one("#chat-view", ChatView).add_message("system", result)
                self._update_status_bar()
                return
            agent_result = self.router.handle_command(text)
            if agent_result is not None:
                chat = self.query_one("#chat-view", ChatView)
                chat.add_message("system", agent_result)
                self._update_status_bar()
                return
            self.query_one("#chat-view", ChatView).add_message(
                "system",
                f"Unknown command: `{text}`\nType `/help` to see all available commands.",
            )
            return

        # Normal message
        chat = self.query_one("#chat-view", ChatView)
        chat.add_message("user", text)
        self._run_agent(text)

    @work(thread=False)
    async def _run_agent(self, user_input: str) -> None:
        chat = self.query_one("#chat-view", ChatView)
        terminal = self.query_one("#terminal-view", TerminalView)
        status = self.query_one("#status-bar", StatusBar)
        context_panel = self.query_one("#context-panel", ContextPanel)

        try:
            config = await self.router.resolve(user_input)
            self._update_status_bar()

            chat.start_loading("thinking")
            assistant_text = ""
            current_msg = None

            async for event in self.engine.submit(user_input):
                if isinstance(event, StatusEvent):
                    if event.status == "thinking":
                        chat.start_loading("thinking")
                    elif event.status == "done":
                        chat.stop_loading()

                elif isinstance(event, TextEvent):
                    if not event.text:
                        continue
                    assistant_text += event.text
                    if current_msg is None:
                        chat.stop_loading()
                        current_msg = chat.add_message("assistant", assistant_text)
                    else:
                        current_msg.update_content(assistant_text)

                elif isinstance(event, ToolCallEvent):
                    chat.start_loading("tool")
                    terminal.log_tool_call(event.name, event.args)
                    status.loading_text = f"▶ {event.name}"

                elif isinstance(event, ToolResultEvent):
                    terminal.log_tool_result(
                        event.name, event.result.content, event.result.is_error
                    )
                    status.loading_text = ""
                    assistant_text = ""
                    current_msg = None

                elif isinstance(event, UsageEvent):
                    model = self.engine.get_model()
                    context_panel.update_usage(
                        input_tokens=event.input_tokens,
                        output_tokens=event.output_tokens,
                        model=model,
                    )
                    # Auto-compact at threshold
                    from nanocode.pricing import context_pct
                    pct = context_pct(model, event.input_tokens)
                    if pct is not None and pct >= _COMPACT_THRESHOLD:
                        self._run_compact(auto=True)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            chat.add_message(
                "system", f"Error: `{type(e).__name__}: {e}`\n```\n{tb}\n```"
            )
        finally:
            chat.stop_loading()
            status.loading_text = ""
            if self.engine.messages:
                self.history.save(
                    self.session_id,
                    self.engine.messages,
                    cwd=os.getcwd(),
                    usage=context_panel.get_stats().to_dict(),
                )

    @work(thread=False)
    async def _run_compact(self, auto: bool = False) -> None:
        chat = self.query_one("#chat-view", ChatView)
        chat.start_loading("thinking")
        try:
            summary = await self.engine.compact()
            label = "Auto-compact" if auto else "Compact"
            chat.add_message(
                "system",
                f"**{label}** — conversation summarized to reduce context.\n\n"
                f"> {summary[:200]}{'...' if len(summary) > 200 else ''}",
            )
            # Save after compact
            context_panel = self.query_one("#context-panel", ContextPanel)
            self.history.save(
                self.session_id,
                self.engine.messages,
                cwd=os.getcwd(),
                usage=context_panel.get_stats().to_dict(),
            )
        except Exception as e:
            chat.add_message("system", f"Compact failed: `{e}`")
        finally:
            chat.stop_loading()

    def _handle_resume(self, text: str) -> None:
        chat = self.query_one("#chat-view", ChatView)
        sessions = self.history.list_sessions()
        parts = text.split()

        if len(parts) == 1:
            chat.add_message("system", format_session_list(sessions))
            return

        try:
            idx = int(parts[1]) - 1
            if idx < 0 or idx >= len(sessions):
                chat.add_message(
                    "system",
                    "Invalid session number. Use `/resume` to list sessions.",
                )
                return
        except ValueError:
            chat.add_message(
                "system",
                "Usage: `/resume` to list, `/resume <n>` to restore.",
            )
            return

        session_id = sessions[idx]["session_id"]
        data = self.history.load(session_id)
        if not data:
            chat.add_message("system", "Session not found or corrupted.")
            return

        # Restore state
        self.engine.messages = data["messages"]
        self.session_id = session_id
        chat.clear_messages()
        for msg in data["messages"]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                chat.add_message(role, content)

        # Restore usage stats
        usage_dict = data.get("usage", {})
        if usage_dict:
            context_panel = self.query_one("#context-panel", ContextPanel)
            context_panel.load_stats(ContextStats.from_dict(usage_dict))

        chat.add_message(
            "system",
            f"Session restored · {len(data['messages'])} messages · `{data.get('cwd', '')}`",
        )

    def _update_status_bar(self) -> None:
        status = self.query_one("#status-bar", StatusBar)
        agent = self.router.current_agent
        model = self.engine.get_model()
        if agent:
            status.set_agent(agent.display_name, agent.color, self.router.mode, model)
        else:
            status.set_agent("none", "#888888", self.router.mode, model)
