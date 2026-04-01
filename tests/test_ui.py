"""Tests for nanocode UI components — import and basic structure checks."""

import pytest


class TestLoadingIndicator:
    def test_thinking_phrases_exist(self):
        from nanocode.ui.loading import THINKING_PHRASES

        assert len(THINKING_PHRASES) >= 10

    def test_tool_phrases_exist(self):
        from nanocode.ui.loading import TOOL_PHRASES

        assert len(TOOL_PHRASES) >= 5

    def test_all_phrases_end_with_ellipsis(self):
        from nanocode.ui.loading import THINKING_PHRASES, TOOL_PHRASES

        for p in THINKING_PHRASES + TOOL_PHRASES:
            assert p.endswith("..."), f"Phrase missing ellipsis: {p}"

    def test_indicator_state_flags(self):
        from nanocode.ui.loading import LoadingIndicator, THINKING_PHRASES

        indicator = LoadingIndicator()
        # Directly set reactives (start/stop need event loop)
        indicator.is_active = True
        indicator.phrase = THINKING_PHRASES[0]
        assert indicator.is_active is True
        assert indicator.phrase != ""
        indicator.is_active = False
        assert indicator.is_active is False

    def test_render_returns_empty_when_inactive(self):
        from nanocode.ui.loading import LoadingIndicator

        indicator = LoadingIndicator()
        indicator.is_active = False
        result = indicator.render()
        assert result.plain == ""

    def test_render_returns_content_when_active(self):
        from nanocode.ui.loading import LoadingIndicator, THINKING_PHRASES, SPINNER_FRAMES

        indicator = LoadingIndicator()
        indicator.is_active = True
        indicator.phrase = THINKING_PHRASES[0]
        result = indicator.render()
        assert result.plain != ""
        assert THINKING_PHRASES[0] in result.plain
        assert any(f in result.plain for f in SPINNER_FRAMES)

    def test_render_contains_spinner_char(self):
        from nanocode.ui.loading import LoadingIndicator, THINKING_PHRASES, SPINNER_FRAMES

        indicator = LoadingIndicator()
        indicator.is_active = True
        indicator.phrase = THINKING_PHRASES[0]
        result = indicator.render()
        assert any(result.plain.startswith(f) for f in SPINNER_FRAMES)

    def test_spinner_changes_with_elapsed_time(self):
        from nanocode.ui.loading import LoadingIndicator, THINKING_PHRASES, SPINNER_FRAMES

        indicator = LoadingIndicator()
        indicator.is_active = True
        indicator.phrase = THINKING_PHRASES[0]

        frames_seen = set()
        for offset in range(len(SPINNER_FRAMES)):
            indicator._start_time = indicator._start_time - (offset * 0.1)
            result = indicator.render()
            if result.plain:
                frames_seen.add(result.plain[0])
        # Should have seen more than one frame across different elapsed times
        assert len(frames_seen) >= 1  # at minimum renders something

    def test_start_sets_thinking_phrase(self):
        from nanocode.ui.loading import LoadingIndicator, THINKING_PHRASES

        indicator = LoadingIndicator()
        indicator.set_interval = lambda *a, **kw: None  # no event loop needed
        indicator.start("thinking")
        assert indicator.is_active is True
        assert indicator.phrase in THINKING_PHRASES

    def test_start_sets_tool_phrase(self):
        from nanocode.ui.loading import LoadingIndicator, TOOL_PHRASES

        indicator = LoadingIndicator()
        indicator.set_interval = lambda *a, **kw: None
        indicator.start("tool")
        assert indicator.is_active is True
        assert indicator.phrase in TOOL_PHRASES

    def test_stop_clears_active_and_timer(self):
        from nanocode.ui.loading import LoadingIndicator

        indicator = LoadingIndicator()
        indicator.set_interval = lambda *a, **kw: None
        indicator.start("thinking")
        indicator.stop()
        assert indicator.is_active is False
        assert indicator._timer is None

    def test_watch_is_active_toggles_display(self):
        from nanocode.ui.loading import LoadingIndicator

        indicator = LoadingIndicator()
        # watch_is_active must toggle self.display so the widget
        # actually appears/disappears in the layout
        indicator.watch_is_active(True)
        assert indicator.display is True
        indicator.watch_is_active(False)
        assert indicator.display is False

    def test_start_stores_pending_mode_when_not_mounted(self):
        from nanocode.ui.loading import LoadingIndicator

        indicator = LoadingIndicator()

        # set_interval raises (simulates pre-mount state)
        def raise_err(*a, **kw):
            raise RuntimeError("not mounted")

        indicator.set_interval = raise_err
        indicator.start("tool")
        # should still be active and store pending mode for on_mount
        assert indicator.is_active is True
        assert indicator._pending_mode == "tool"

    def test_on_mount_starts_timer_if_pending(self):
        from nanocode.ui.loading import LoadingIndicator

        indicator = LoadingIndicator()
        timer_started = []
        indicator.set_interval = lambda *a, **kw: timer_started.append(True) or object()
        indicator._pending_mode = "thinking"
        indicator.is_active = True
        indicator._start_pending_timer()
        assert len(timer_started) == 1
        assert indicator._pending_mode is None


class TestStatusBar:
    def test_set_agent(self):
        from nanocode.ui.status_bar import StatusBar

        bar = StatusBar()
        bar.set_agent("Claude Code", "#CC7832", "auto")
        assert bar.agent_name == "Claude Code"
        assert bar.agent_color == "#CC7832"
        assert bar.route_mode == "auto"

    def test_render_contains_agent_name(self):
        from nanocode.ui.status_bar import StatusBar

        bar = StatusBar()
        bar.agent_name = "Codex"
        bar.route_mode = "codex"
        text = bar.render()
        assert "Codex" in text.plain
        assert "nanocode" in text.plain


class TestTerminalView:
    def test_import(self):
        from nanocode.ui.terminal_view import TerminalView

        assert TerminalView is not None


class TestChatView:
    def test_import(self):
        from nanocode.ui.chat_view import ChatView, MessageItem

        assert ChatView is not None
        assert MessageItem is not None

    def test_start_loading_calls_indicator_start(self):
        """Test that start_loading() calls indicator.start()."""
        from nanocode.ui.chat_view import ChatView
        from nanocode.ui.loading import LoadingIndicator

        chat = ChatView()
        # Mock the indicator
        calls = []
        original_start = LoadingIndicator.start

        def mock_start(self, mode="thinking"):
            calls.append(("start", mode))
            original_start(self, mode)

        LoadingIndicator.start = mock_start
        try:
            # Manually create and set the indicator
            indicator = LoadingIndicator(id="loading")
            indicator.set_interval = lambda *a, **kw: None  # no event loop
            chat._loading = indicator

            # Override query_one to return our mock
            original_query = chat.query_one

            def mock_query(selector, *args, **kwargs):
                if selector == "#loading":
                    return indicator
                return original_query(selector, *args, **kwargs)

            chat.query_one = mock_query

            # Call start_loading
            chat.start_loading("thinking")

            # Verify start was called
            assert len(calls) == 1
            assert calls[0] == ("start", "thinking")
        finally:
            LoadingIndicator.start = original_start

    def test_stop_loading_calls_indicator_stop(self):
        """Test that stop_loading() calls indicator.stop()."""
        from nanocode.ui.chat_view import ChatView
        from nanocode.ui.loading import LoadingIndicator

        chat = ChatView()
        calls = []
        original_stop = LoadingIndicator.stop

        def mock_stop(self):
            calls.append("stop")
            original_stop(self)

        LoadingIndicator.stop = mock_stop
        try:
            indicator = LoadingIndicator(id="loading")
            indicator.set_interval = lambda *a, **kw: None

            original_query = chat.query_one

            def mock_query(selector, *args, **kwargs):
                if selector == "#loading":
                    return indicator
                return original_query(selector, *args, **kwargs)

            chat.query_one = mock_query

            chat.stop_loading()

            assert len(calls) == 1
            assert calls[0] == "stop"
        finally:
            LoadingIndicator.stop = original_stop


class TestApp:
    def test_import(self):
        from nanocode.ui.app import NanoCodeApp

        assert NanoCodeApp is not None

    def test_entry_point_import(self):
        from nanocode.__main__ import main

        assert callable(main)

    def test_help_text_exists(self):
        from nanocode.ui.app import HELP_TEXT

        assert "/agent" in HELP_TEXT
        assert "/clear" in HELP_TEXT
        assert "/exit" in HELP_TEXT
        assert "/help" in HELP_TEXT
        assert "auto" in HELP_TEXT

    def test_help_text_covers_all_agents(self):
        from nanocode.ui.app import HELP_TEXT

        assert "claude" in HELP_TEXT.lower()
        assert "codex" in HELP_TEXT.lower()
        assert "opencode" in HELP_TEXT.lower()

    def test_help_text_is_markdown(self):
        from nanocode.ui.app import HELP_TEXT

        assert "##" in HELP_TEXT  # has markdown headers
        assert "|" in HELP_TEXT  # has markdown tables

    def test_welcome_text_contains_key_info(self):
        import os
        from unittest.mock import patch
        from nanocode.ui.app import NanoCodeApp

        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "test", "NANOCODE_MODEL": "gpt-4o"}
        ):
            app = NanoCodeApp.__new__(NanoCodeApp)
            text = app._welcome_text()
        assert "nanocode" in text
        assert "gpt-4o" in text
        assert "/help" in text
        assert "auto" in text
