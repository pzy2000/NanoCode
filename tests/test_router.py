"""Tests for nanocode router — written BEFORE implementation (TDD)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRouterCommands:
    def test_handle_agent_switch(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine)

        result = router.handle_command("/agent claude")
        assert result is not None
        assert "claude" in result.lower()
        assert router.mode == "claude"

    def test_handle_agent_auto(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine)
        router.mode = "claude"

        result = router.handle_command("/agent auto")
        assert router.mode == "auto"

    def test_handle_agent_unknown(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine)

        result = router.handle_command("/agent foobar")
        assert result is not None
        assert "unknown" in result.lower() or "foobar" in result.lower()
        assert router.mode == "auto"  # unchanged

    def test_handle_agent_no_arg_shows_status(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine)

        result = router.handle_command("/agent")
        assert result is not None
        assert "auto" in result.lower()  # shows current mode

    def test_non_agent_command_returns_none(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine)

        assert router.handle_command("hello world") is None
        assert router.handle_command("/clear") is None

    def test_switch_configures_engine(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")

        router.handle_command("/agent codex")
        engine.configure.assert_called_once()
        config = engine.configure.call_args[0][0]
        assert config.name == "codex"

    def test_switch_same_agent_no_reconfigure(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")

        router.handle_command("/agent claude")
        router.handle_command("/agent claude")
        # Should only configure once (already on claude)
        assert engine.configure.call_count == 1


class TestRouterResolve:
    @pytest.mark.asyncio
    async def test_resolve_manual_mode(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")
        router.mode = "codex"

        config = await router.resolve("write some code")
        assert config.name == "codex"

    @pytest.mark.asyncio
    async def test_resolve_auto_calls_classify(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")
        router.mode = "auto"
        router._classify = AsyncMock(return_value="claude")

        config = await router.resolve("explain this code")
        router._classify.assert_called_once_with("explain this code")
        assert config.name == "claude"

    @pytest.mark.asyncio
    async def test_resolve_auto_fallback_on_bad_classify(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")
        router.mode = "auto"
        router._classify = AsyncMock(return_value="garbage")

        config = await router.resolve("do something")
        assert config.name == "claude"  # fallback

    @pytest.mark.asyncio
    async def test_resolve_configures_engine_on_switch(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")
        router.mode = "auto"
        router._classify = AsyncMock(return_value="codex")

        await router.resolve("build the project")
        engine.configure.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_no_reconfigure_same_agent(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")
        router.mode = "auto"
        router._classify = AsyncMock(return_value="claude")

        await router.resolve("first question")
        await router.resolve("second question")
        # Second call should not reconfigure if same agent
        assert engine.configure.call_count == 1


class TestRouterCurrentAgent:
    def test_initial_state(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine)
        assert router.mode == "auto"
        assert router.current_agent is None

    @pytest.mark.asyncio
    async def test_current_agent_after_resolve(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")
        router.mode = "claude"

        config = await router.resolve("hi")
        assert router.current_agent is not None
        assert router.current_agent.name == "claude"

    def test_current_agent_after_command(self):
        from nanocode.router import Router

        engine = MagicMock()
        router = Router(engine, cwd="/tmp")

        router.handle_command("/agent opencode")
        assert router.current_agent is not None
        assert router.current_agent.name == "opencode"


class TestRouterPrompt:
    def test_router_prompt_exists(self):
        from nanocode.router import ROUTER_PROMPT

        assert "claude" in ROUTER_PROMPT.lower()
        assert "codex" in ROUTER_PROMPT.lower()
        assert "opencode" in ROUTER_PROMPT.lower()
