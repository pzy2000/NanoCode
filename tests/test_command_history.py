"""Tests for CommandHistory — persistent cross-session command history."""

from __future__ import annotations

import pytest

from nanocode.ui.command_history import CommandHistory


@pytest.fixture
def tmp_history_path(tmp_path):
    return tmp_path / "command_history.json"


@pytest.fixture
def history(tmp_history_path):
    return CommandHistory(path=tmp_history_path)


class TestCommandHistoryAdd:
    def test_add_single_entry(self, history):
        history.add("hello world")
        assert history.entries == ["hello world"]

    def test_add_multiple_entries(self, history):
        history.add("first")
        history.add("second")
        history.add("third")
        assert history.entries == ["first", "second", "third"]

    def test_dedup_consecutive(self, history):
        history.add("same")
        history.add("same")
        assert history.entries == ["same"]

    def test_dedup_non_consecutive_allowed(self, history):
        history.add("a")
        history.add("b")
        history.add("a")
        assert history.entries == ["a", "b", "a"]

    def test_ignore_empty_string(self, history):
        history.add("")
        history.add("  ")
        assert history.entries == []

    def test_max_size_respected(self, tmp_history_path):
        h = CommandHistory(path=tmp_history_path, max_size=3)
        h.add("a")
        h.add("b")
        h.add("c")
        h.add("d")
        assert len(h.entries) == 3
        assert h.entries == ["b", "c", "d"]


class TestCommandHistoryNavigation:
    def test_navigate_up_returns_last_entry(self, history):
        history.add("first")
        history.add("second")
        assert history.navigate_up() == "second"

    def test_navigate_up_twice(self, history):
        history.add("first")
        history.add("second")
        history.navigate_up()
        assert history.navigate_up() == "first"

    def test_navigate_up_clamps_at_oldest(self, history):
        history.add("only")
        history.navigate_up()
        assert history.navigate_up() == "only"

    def test_navigate_down_after_up(self, history):
        history.add("first")
        history.add("second")
        history.navigate_up()
        history.navigate_up()
        assert history.navigate_down() == "second"

    def test_navigate_down_at_end_returns_none(self, history):
        history.add("first")
        history.navigate_up()
        assert history.navigate_down() is None

    def test_navigate_empty_history_returns_none(self, history):
        assert history.navigate_up() is None
        assert history.navigate_down() is None

    def test_add_resets_navigation_position(self, history):
        history.add("first")
        history.add("second")
        history.navigate_up()  # at "second"
        history.add("third")
        assert history.navigate_up() == "third"

    def test_reset_clears_navigation_position(self, history):
        history.add("first")
        history.add("second")
        history.navigate_up()
        history.reset()
        assert history.navigate_up() == "second"


class TestCommandHistoryPersistence:
    def test_save_and_load(self, tmp_history_path):
        h1 = CommandHistory(path=tmp_history_path)
        h1.add("cmd1")
        h1.add("cmd2")
        h1.save()

        h2 = CommandHistory(path=tmp_history_path)
        assert h2.entries == ["cmd1", "cmd2"]

    def test_load_missing_file_starts_empty(self, tmp_history_path):
        h = CommandHistory(path=tmp_history_path)
        assert h.entries == []

    def test_load_corrupted_file_starts_empty(self, tmp_history_path):
        tmp_history_path.write_text("not valid json")
        h = CommandHistory(path=tmp_history_path)
        assert h.entries == []

    def test_save_creates_parent_dirs(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "history.json"
        h = CommandHistory(path=deep_path)
        h.add("cmd")
        h.save()
        assert deep_path.exists()

    def test_cross_session_persistence(self, tmp_history_path):
        h1 = CommandHistory(path=tmp_history_path)
        h1.add("session1_cmd")
        h1.save()

        h2 = CommandHistory(path=tmp_history_path)
        h2.add("session2_cmd")
        h2.save()

        h3 = CommandHistory(path=tmp_history_path)
        assert "session1_cmd" in h3.entries
        assert "session2_cmd" in h3.entries
