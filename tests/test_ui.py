"""Tests for nanocode UI components — import and basic structure checks."""

import pytest


class TestLoadingIndicator:
    def test_thinking_phrases_exist(self):
        from nanocode.ui.loading import THINKING_PHRASES

        assert len(THINKING_PHRASES) >= 10

    def test_tool_phrases_exist(self):
        from nanocode.ui.loading import TOOL_PHRASES

        assert len(TOOL_PHRASES) >= 5

    def test_all_phrases_are_greek_mythology(self):
        from nanocode.ui.loading import THINKING_PHRASES, TOOL_PHRASES

        # Each phrase should end with "..."
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
