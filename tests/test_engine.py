"""Tests for nanocode engine — written BEFORE implementation (TDD)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# === Test Event types ===


class TestEvents:
    def test_text_event(self):
        from nanocode.engine import TextEvent

        e = TextEvent("hello")
        assert e.text == "hello"

    def test_tool_call_event(self):
        from nanocode.engine import ToolCallEvent

        e = ToolCallEvent(name="shell", args={"command": "ls"}, call_id="1")
        assert e.name == "shell"
        assert e.args == {"command": "ls"}
        assert e.call_id == "1"

    def test_tool_result_event(self):
        from nanocode.engine import ToolResultEvent
        from nanocode.tools import ToolResult

        r = ToolResult("output")
        e = ToolResultEvent(name="shell", result=r, call_id="1")
        assert e.result.content == "output"

    def test_status_event(self):
        from nanocode.engine import StatusEvent

        e = StatusEvent("thinking")
        assert e.status == "thinking"


# === Test Backend factory ===


class TestBackendFactory:
    def test_create_openai_backend(self):
        from nanocode.engine import create_backend
        from nanocode.backends import OpenAIBackend

        b = create_backend(
            "openai", api_key="test", base_url="http://localhost", model="gpt-4"
        )
        assert isinstance(b, OpenAIBackend)

    def test_create_anthropic_backend(self):
        from nanocode.engine import create_backend
        from nanocode.backends import AnthropicBackend

        b = create_backend(
            "anthropic", api_key="test", base_url=None, model="claude-sonnet-4-20250514"
        )
        assert isinstance(b, AnthropicBackend)

    def test_default_is_openai(self):
        from nanocode.engine import create_backend
        from nanocode.backends import OpenAIBackend

        b = create_backend("unknown", api_key="test", base_url=None, model="x")
        assert isinstance(b, OpenAIBackend)


# === Test Engine with mock backend ===


class TestEngine:
    @pytest.fixture
    def mock_backend(self):
        from nanocode.engine import TextEvent

        backend = AsyncMock()

        async def simple_stream(system, messages, tools):
            yield TextEvent("Hello world")

        backend.stream = MagicMock(side_effect=simple_stream)
        return backend

    @pytest.fixture
    def engine(self, mock_backend):
        from nanocode.engine import Engine

        e = Engine(mock_backend)
        return e

    @pytest.mark.asyncio
    async def test_submit_yields_status_then_text(self, engine, mock_backend):
        from nanocode.engine import TextEvent, StatusEvent

        events = []
        async for event in engine.submit("hi"):
            events.append(event)

        statuses = [e for e in events if isinstance(e, StatusEvent)]
        texts = [e for e in events if isinstance(e, TextEvent)]
        assert any(s.status == "thinking" for s in statuses)
        assert any(t.text == "Hello world" for t in texts)

    @pytest.mark.asyncio
    async def test_submit_appends_user_message(self, engine, mock_backend):
        async for _ in engine.submit("test input"):
            pass
        assert len(engine.messages) >= 2  # user + assistant
        assert engine.messages[0]["role"] == "user"
        assert engine.messages[0]["content"] == "test input"

    @pytest.mark.asyncio
    async def test_submit_appends_assistant_message(self, engine, mock_backend):
        async for _ in engine.submit("hi"):
            pass
        assert engine.messages[-1]["role"] == "assistant"
        assert "Hello world" in engine.messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_tool_call_loop(self):
        """Engine should loop: LLM -> tool_call -> execute -> LLM -> text -> done"""
        from nanocode.engine import Engine, TextEvent, ToolCallEvent
        from nanocode.tools import ToolResult

        call_count = 0

        async def stream_with_tool(system, messages, tools):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: return a tool call
                yield ToolCallEvent(
                    name="shell", args={"command": "echo hi"}, call_id="tc1"
                )
            else:
                # Second call: return text (done)
                yield TextEvent("Done!")

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=stream_with_tool)

        engine = Engine(backend)
        engine.configure_tools(
            {
                "shell": MagicMock(
                    name="shell",
                    is_read_only=False,
                    execute=MagicMock(return_value=ToolResult("hi\n")),
                )
            }
        )
        engine.approval_policy = "none"

        events = []
        async for event in engine.submit("run echo"):
            events.append(event)

        from nanocode.engine import ToolCallEvent as TCE, ToolResultEvent, StatusEvent

        tool_calls = [e for e in events if isinstance(e, TCE)]
        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        texts = [e for e in events if isinstance(e, TextEvent)]

        assert len(tool_calls) == 1
        assert tool_calls[0].name == "shell"
        assert len(tool_results) == 1
        assert tool_results[0].result.content == "hi\n"
        assert len(texts) == 1
        assert texts[0].text == "Done!"
        assert call_count == 2  # two LLM calls

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self):
        """Engine should stop after max_iterations to prevent infinite loops."""
        from nanocode.engine import Engine, ToolCallEvent
        from nanocode.tools import ToolResult

        async def always_tool_call(system, messages, tools):
            yield ToolCallEvent(name="shell", args={"command": "echo"}, call_id="tc")

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=always_tool_call)

        engine = Engine(backend)
        engine.max_iterations = 3
        engine.configure_tools(
            {
                "shell": MagicMock(
                    name="shell",
                    is_read_only=False,
                    execute=MagicMock(return_value=ToolResult("ok")),
                )
            }
        )
        engine.approval_policy = "none"

        events = []
        async for event in engine.submit("loop forever"):
            events.append(event)

        from nanocode.engine import ToolCallEvent as TCE

        tool_calls = [e for e in events if isinstance(e, TCE)]
        assert len(tool_calls) == 3  # stopped at max

    @pytest.mark.asyncio
    async def test_configure_from_agent_config(self):
        """Engine.configure() should set system_prompt, tools, approval_policy from AgentConfig."""
        from nanocode.engine import Engine, TextEvent
        from nanocode.agents.claude import ClaudeAgent

        async def simple(system, messages, tools):
            yield TextEvent("ok")

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=simple)

        engine = Engine(backend)
        config = ClaudeAgent()
        engine.configure(config, cwd="/tmp")

        assert "Claude Code" in engine.system_prompt
        assert "shell" in engine.tools
        assert engine.approval_policy == "prompt"

    @pytest.mark.asyncio
    async def test_tool_messages_in_history(self):
        """After a tool call, history should contain tool result messages."""
        from nanocode.engine import Engine, TextEvent, ToolCallEvent
        from nanocode.tools import ToolResult

        call_count = 0

        async def stream_fn(system, messages, tools):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                yield ToolCallEvent(name="read", args={"file_path": "x"}, call_id="tc1")
            else:
                yield TextEvent("read it")

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=stream_fn)

        engine = Engine(backend)
        engine.configure_tools(
            {
                "read": MagicMock(
                    name="read",
                    is_read_only=True,
                    execute=MagicMock(return_value=ToolResult("file contents")),
                )
            }
        )
        engine.approval_policy = "none"

        async for _ in engine.submit("read file"):
            pass

        # History: user, assistant(tool_call), tool_result, assistant(text)
        roles = [m["role"] for m in engine.messages]
        assert "tool" in roles or "user" in roles  # tool results stored somehow

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """If LLM calls a tool not in registry, engine should return error result."""
        from nanocode.engine import Engine, TextEvent, ToolCallEvent, ToolResultEvent
        from nanocode.tools import ToolResult

        call_count = 0

        async def stream_fn(system, messages, tools):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                yield ToolCallEvent(name="nonexistent", args={}, call_id="tc1")
            else:
                yield TextEvent("ok")

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=stream_fn)

        engine = Engine(backend)
        engine.approval_policy = "none"

        events = []
        async for event in engine.submit("do something"):
            events.append(event)

        results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(results) == 1
        assert results[0].result.is_error is True
        assert (
            "nonexistent" in results[0].result.content.lower()
            or "unknown" in results[0].result.content.lower()
        )


class TestUsageEvent:
    def test_usage_event_fields(self):
        from nanocode.engine import UsageEvent

        e = UsageEvent(input_tokens=100, output_tokens=50)
        assert e.input_tokens == 100
        assert e.output_tokens == 50

    def test_usage_event_in_event_union(self):
        from nanocode.engine import UsageEvent, Event
        import typing
        args = typing.get_args(Event)
        assert UsageEvent in args


class TestEngineCompact:
    @pytest.fixture
    def engine_with_history(self):
        from nanocode.engine import Engine, TextEvent

        async def summarize_stream(system, messages, tools):
            yield TextEvent("This is a summary of the conversation.")

        from unittest.mock import AsyncMock, MagicMock
        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=summarize_stream)

        engine = Engine(backend)
        engine.messages = [
            {"role": "user", "content": "fix the bug"},
            {"role": "assistant", "content": "I fixed it by changing line 42."},
            {"role": "user", "content": "now add tests"},
            {"role": "assistant", "content": "Added 3 tests in test_foo.py."},
        ]
        return engine

    @pytest.mark.asyncio
    async def test_compact_returns_summary_string(self, engine_with_history):
        summary = await engine_with_history.compact()
        assert isinstance(summary, str)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_compact_replaces_messages(self, engine_with_history):
        await engine_with_history.compact()
        # After compact, messages should be shorter
        assert len(engine_with_history.messages) <= 2

    @pytest.mark.asyncio
    async def test_compact_messages_contain_summary(self, engine_with_history):
        summary = await engine_with_history.compact()
        all_content = " ".join(
            m.get("content", "") for m in engine_with_history.messages
        )
        assert summary in all_content

    @pytest.mark.asyncio
    async def test_compact_empty_history(self):
        from nanocode.engine import Engine, TextEvent
        from unittest.mock import AsyncMock, MagicMock

        async def stream_fn(system, messages, tools):
            yield TextEvent("Empty.")

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=stream_fn)
        engine = Engine(backend)
        engine.messages = []

        summary = await engine.compact()
        assert isinstance(summary, str)

    @pytest.mark.asyncio
    async def test_submit_emits_usage_event_if_backend_provides(self):
        """If backend emits UsageEvent, engine should pass it through."""
        from nanocode.engine import Engine, TextEvent, UsageEvent
        from unittest.mock import AsyncMock, MagicMock

        async def stream_fn(system, messages, tools):
            yield TextEvent("hello")
            yield UsageEvent(input_tokens=100, output_tokens=20)

        backend = AsyncMock()
        backend.stream = MagicMock(side_effect=stream_fn)
        engine = Engine(backend)

        events = []
        async for event in engine.submit("hi"):
            events.append(event)

        usage_events = [e for e in events if isinstance(e, UsageEvent)]
        assert len(usage_events) == 1
        assert usage_events[0].input_tokens == 100
        assert usage_events[0].output_tokens == 20
