"""Tests for SlashCompleter — Tab autocomplete for slash commands."""

from __future__ import annotations

import pytest

from nanocode.ui.autocomplete import SlashCompleter


@pytest.fixture
def completer():
    return SlashCompleter()


class TestSlashCompleterCommands:
    def test_empty_input_returns_all_commands(self, completer):
        results = completer.complete("/")
        commands = [r.value for r in results]
        assert "/agent" in commands
        assert "/model" in commands
        assert "/resume" in commands
        assert "/clear" in commands
        assert "/help" in commands
        assert "/exit" in commands

    def test_prefix_filters_commands(self, completer):
        results = completer.complete("/ag")
        assert len(results) == 1
        assert results[0].value == "/agent"

    def test_prefix_filters_multiple(self, completer):
        results = completer.complete("/")
        assert len(results) >= 6

    def test_no_match_returns_empty(self, completer):
        results = completer.complete("/zzz")
        assert results == []

    def test_non_slash_input_returns_empty(self, completer):
        results = completer.complete("hello")
        assert results == []

    def test_empty_input_returns_empty(self, completer):
        results = completer.complete("")
        assert results == []

    def test_exact_command_returns_itself(self, completer):
        results = completer.complete("/clear")
        assert any(r.value == "/clear" for r in results)


class TestSlashCompleterArguments:
    def test_agent_subcommands(self, completer):
        results = completer.complete("/agent ")
        values = [r.value for r in results]
        assert "/agent auto" in values
        assert "/agent claude" in values
        assert "/agent codex" in values
        assert "/agent opencode" in values

    def test_agent_subcommand_prefix_filter(self, completer):
        results = completer.complete("/agent cl")
        assert len(results) == 1
        assert results[0].value == "/agent claude"

    def test_model_subcommands(self, completer):
        results = completer.complete("/model ")
        values = [r.value for r in results]
        assert any("gpt" in v or "claude" in v for v in values)

    def test_resume_no_subcommands(self, completer):
        # /resume takes a number, no static completions
        results = completer.complete("/resume ")
        assert results == []


class TestCompletionItem:
    def test_completion_item_has_value_and_description(self, completer):
        results = completer.complete("/agent ")
        for item in results:
            assert hasattr(item, "value")
            assert hasattr(item, "description")
            assert item.value != ""


class TestSlashCompleterCycling:
    def test_next_cycles_through_completions(self, completer):
        completer.complete("/agent ")
        first = completer.next()
        second = completer.next()
        assert first is not None
        assert second is not None
        assert first.value != second.value

    def test_next_wraps_around(self, completer):
        results = completer.complete("/ag")
        # Only one result — next should return same item repeatedly
        first = completer.next()
        second = completer.next()
        assert first.value == second.value

    def test_next_returns_none_when_no_completions(self, completer):
        completer.complete("/zzz")
        assert completer.next() is None

    def test_reset_clears_state(self, completer):
        completer.complete("/agent ")
        completer.next()
        completer.reset()
        assert completer._results == []
        assert completer._index == 0
