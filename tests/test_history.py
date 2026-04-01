"""Tests for nanocode history — written BEFORE implementation (TDD)."""

import json
import time
from pathlib import Path

import pytest


class TestHistoryManager:
    def test_save_creates_file(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save(
            session_id="abc123",
            messages=[{"role": "user", "content": "hi"}],
            cwd="/tmp",
        )
        assert (tmp_path / "abc123.json").exists()

    def test_save_and_load_roundtrip(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        hm.save("sess1", messages, cwd="/tmp")
        loaded = hm.load("sess1")
        assert loaded["messages"] == messages
        assert loaded["session_id"] == "sess1"

    def test_load_nonexistent_returns_none(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        assert hm.load("doesnotexist") is None

    def test_list_sessions_empty(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        assert hm.list_sessions() == []

    def test_list_sessions_returns_metadata(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save("s1", [{"role": "user", "content": "first message"}], cwd="/proj")
        hm.save("s2", [{"role": "user", "content": "second message"}], cwd="/proj")
        sessions = hm.list_sessions()
        assert len(sessions) == 2
        ids = {s["session_id"] for s in sessions}
        assert "s1" in ids
        assert "s2" in ids

    def test_list_sessions_sorted_newest_first(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save("old", [{"role": "user", "content": "old"}], cwd="/tmp")
        time.sleep(0.01)
        hm.save("new", [{"role": "user", "content": "new"}], cwd="/tmp")
        sessions = hm.list_sessions()
        assert sessions[0]["session_id"] == "new"

    def test_session_metadata_has_preview(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save(
            "s1", [{"role": "user", "content": "fix the bug in parser.py"}], cwd="/tmp"
        )
        sessions = hm.list_sessions()
        assert "fix the bug" in sessions[0]["preview"]

    def test_session_metadata_has_timestamp(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save("s1", [{"role": "user", "content": "hi"}], cwd="/tmp")
        sessions = hm.list_sessions()
        assert "timestamp" in sessions[0]

    def test_session_metadata_has_cwd(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save("s1", [{"role": "user", "content": "hi"}], cwd="/my/project")
        sessions = hm.list_sessions()
        assert sessions[0]["cwd"] == "/my/project"

    def test_session_metadata_has_message_count(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        msgs = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
        hm.save("s1", msgs, cwd="/tmp")
        sessions = hm.list_sessions()
        assert sessions[0]["message_count"] == 2

    def test_delete_session(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save("s1", [{"role": "user", "content": "hi"}], cwd="/tmp")
        hm.delete("s1")
        assert hm.load("s1") is None
        assert len(hm.list_sessions()) == 0

    def test_default_base_dir(self):
        from nanocode.history import HistoryManager

        hm = HistoryManager()
        assert str(hm.base_dir).endswith(".nanocode/history")

    def test_base_dir_created_on_init(self, tmp_path):
        from nanocode.history import HistoryManager

        new_dir = tmp_path / "deep" / "nested"
        hm = HistoryManager(base_dir=new_dir)
        assert new_dir.exists()


class TestSessionId:
    def test_generate_session_id_is_unique(self):
        from nanocode.history import generate_session_id

        ids = {generate_session_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_session_id_is_string(self):
        from nanocode.history import generate_session_id

        sid = generate_session_id()
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_generate_session_id_url_safe(self):
        from nanocode.history import generate_session_id

        sid = generate_session_id()
        # Should be usable as a filename
        assert "/" not in sid
        assert "\\" not in sid
        assert " " not in sid


class TestResumeCommand:
    def test_format_session_list_empty(self):
        from nanocode.history import format_session_list

        result = format_session_list([])
        assert "no" in result.lower() or "empty" in result.lower()

    def test_format_session_list_shows_index(self):
        from nanocode.history import format_session_list

        sessions = [
            {
                "session_id": "abc",
                "preview": "fix the bug",
                "timestamp": "2025-03-31T10:00:00",
                "cwd": "/proj",
                "message_count": 4,
            },
        ]
        result = format_session_list(sessions)
        assert "1" in result
        assert "fix the bug" in result

    def test_format_session_list_shows_multiple(self):
        from nanocode.history import format_session_list

        sessions = [
            {
                "session_id": "a",
                "preview": "first task",
                "timestamp": "2025-03-31T10:00:00",
                "cwd": "/p",
                "message_count": 2,
            },
            {
                "session_id": "b",
                "preview": "second task",
                "timestamp": "2025-03-31T11:00:00",
                "cwd": "/p",
                "message_count": 6,
            },
        ]
        result = format_session_list(sessions)
        assert "first task" in result
        assert "second task" in result
        assert "1" in result
        assert "2" in result


class TestHistoryUsagePersistence:
    def test_save_with_usage(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        usage = {"total_input_tokens": 3313, "total_output_tokens": 512, "total_cost": 0.64, "last_input_tokens": 3313}
        hm.save("s1", [{"role": "user", "content": "hi"}], cwd="/tmp", usage=usage)
        loaded = hm.load("s1")
        assert loaded["usage"]["total_input_tokens"] == 3313
        assert abs(loaded["usage"]["total_cost"] - 0.64) < 1e-6

    def test_save_without_usage_defaults_empty(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        hm.save("s1", [{"role": "user", "content": "hi"}], cwd="/tmp")
        loaded = hm.load("s1")
        assert "usage" in loaded
        assert loaded["usage"]["total_input_tokens"] == 0
        assert loaded["usage"]["total_cost"] == 0.0

    def test_usage_in_session_metadata(self, tmp_path):
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        usage = {"total_input_tokens": 1000, "total_output_tokens": 200, "total_cost": 0.10, "last_input_tokens": 1000}
        hm.save("s1", [{"role": "user", "content": "hi"}], cwd="/tmp", usage=usage)
        sessions = hm.list_sessions()
        assert sessions[0]["usage"]["total_cost"] == 0.10

    def test_resume_preserves_usage(self, tmp_path):
        """Loading a session should return the saved usage dict intact."""
        from nanocode.history import HistoryManager

        hm = HistoryManager(base_dir=tmp_path)
        usage = {"total_input_tokens": 5000, "total_output_tokens": 800, "total_cost": 1.23, "last_input_tokens": 5000}
        hm.save("s1", [{"role": "user", "content": "test"}], cwd="/tmp", usage=usage)
        loaded = hm.load("s1")
        assert loaded["usage"]["total_output_tokens"] == 800
        assert abs(loaded["usage"]["total_cost"] - 1.23) < 1e-6
