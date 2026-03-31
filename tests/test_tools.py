"""Tests for nanocode tools — written BEFORE implementation (TDD)."""

import os
import tempfile
from pathlib import Path

import pytest


# === Test Tool base classes ===


class TestToolResult:
    def test_success_result(self):
        from nanocode.tools import ToolResult

        r = ToolResult("hello")
        assert r.content == "hello"
        assert r.is_error is False

    def test_error_result(self):
        from nanocode.tools import ToolResult

        r = ToolResult("boom", is_error=True)
        assert r.content == "boom"
        assert r.is_error is True


class TestToolABC:
    def test_tool_has_required_interface(self):
        from nanocode.tools import Tool

        # Tool is abstract — can't instantiate directly
        with pytest.raises(TypeError):
            Tool()

    def test_concrete_tool_works(self):
        from nanocode.tools import Tool, ToolResult

        class DummyTool(Tool):
            name = "dummy"
            description = "A dummy tool"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **kwargs) -> ToolResult:
                return ToolResult("ok")

        t = DummyTool()
        assert t.name == "dummy"
        assert t.execute().content == "ok"
        assert t.is_read_only is False

    def test_openai_schema(self):
        from nanocode.tools import Tool, ToolResult

        class DummyTool(Tool):
            name = "dummy"
            description = "A dummy"
            parameters = {"type": "object", "properties": {"x": {"type": "string"}}}

            def execute(self, **kwargs) -> ToolResult:
                return ToolResult("ok")

        schema = DummyTool().to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "dummy"
        assert "x" in schema["function"]["parameters"]["properties"]

    def test_anthropic_schema(self):
        from nanocode.tools import Tool, ToolResult

        class DummyTool(Tool):
            name = "dummy"
            description = "A dummy"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **kwargs) -> ToolResult:
                return ToolResult("ok")

        schema = DummyTool().to_anthropic_schema()
        assert schema["name"] == "dummy"
        assert "input_schema" in schema


# === Test Tool Registry ===


class TestToolRegistry:
    def test_registry_has_all_tools(self):
        from nanocode.tools import TOOL_REGISTRY

        expected = {"shell", "read", "write", "edit", "glob", "grep"}
        assert set(TOOL_REGISTRY.keys()) == expected

    def test_get_tools_by_names(self):
        from nanocode.tools import get_tools

        tools = get_tools(["shell", "read"])
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"shell", "read"}

    def test_get_tools_unknown_name_skipped(self):
        from nanocode.tools import get_tools

        tools = get_tools(["shell", "nonexistent"])
        assert len(tools) == 1


# === Test ShellTool ===


class TestShellTool:
    def test_simple_command(self):
        from nanocode.tools import TOOL_REGISTRY

        shell = TOOL_REGISTRY["shell"]
        result = shell.execute(command="echo hello")
        assert "hello" in result.content
        assert result.is_error is False

    def test_failing_command(self):
        from nanocode.tools import TOOL_REGISTRY

        shell = TOOL_REGISTRY["shell"]
        result = shell.execute(command="false")
        assert result.is_error is True

    def test_workdir(self):
        from nanocode.tools import TOOL_REGISTRY

        shell = TOOL_REGISTRY["shell"]
        result = shell.execute(command="pwd", workdir="/tmp")
        # macOS /tmp -> /private/tmp
        assert "tmp" in result.content

    def test_shell_is_not_read_only(self):
        from nanocode.tools import TOOL_REGISTRY

        assert TOOL_REGISTRY["shell"].is_read_only is False


# === Test FileReadTool ===


class TestFileReadTool:
    def test_read_file(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        result = TOOL_REGISTRY["read"].execute(file_path=str(f))
        assert "1: line1" in result.content
        assert "2: line2" in result.content
        assert result.is_error is False

    def test_read_with_offset_limit(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "test.txt"
        f.write_text("a\nb\nc\nd\ne\n")
        result = TOOL_REGISTRY["read"].execute(file_path=str(f), offset=2, limit=2)
        assert "2: b" in result.content
        assert "3: c" in result.content
        assert "1: a" not in result.content

    def test_read_nonexistent(self):
        from nanocode.tools import TOOL_REGISTRY

        result = TOOL_REGISTRY["read"].execute(file_path="/nonexistent/file.txt")
        assert result.is_error is True

    def test_read_is_read_only(self):
        from nanocode.tools import TOOL_REGISTRY

        assert TOOL_REGISTRY["read"].is_read_only is True


# === Test FileWriteTool ===


class TestFileWriteTool:
    def test_write_file(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "out.txt"
        result = TOOL_REGISTRY["write"].execute(file_path=str(f), content="hello world")
        assert result.is_error is False
        assert f.read_text() == "hello world"

    def test_write_creates_dirs(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "sub" / "dir" / "out.txt"
        result = TOOL_REGISTRY["write"].execute(file_path=str(f), content="nested")
        assert result.is_error is False
        assert f.read_text() == "nested"

    def test_write_is_not_read_only(self):
        from nanocode.tools import TOOL_REGISTRY

        assert TOOL_REGISTRY["write"].is_read_only is False


# === Test FileEditTool ===


class TestFileEditTool:
    def test_edit_replaces_string(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "code.py"
        f.write_text("def foo():\n    return 1\n")
        result = TOOL_REGISTRY["edit"].execute(
            file_path=str(f), old_string="return 1", new_string="return 2"
        )
        assert result.is_error is False
        assert "return 2" in f.read_text()

    def test_edit_old_string_not_found(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "code.py"
        f.write_text("hello")
        result = TOOL_REGISTRY["edit"].execute(
            file_path=str(f), old_string="nonexistent", new_string="x"
        )
        assert result.is_error is True

    def test_edit_is_not_read_only(self):
        from nanocode.tools import TOOL_REGISTRY

        assert TOOL_REGISTRY["edit"].is_read_only is False


# === Test GlobTool ===


class TestGlobTool:
    def test_glob_finds_files(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        (tmp_path / "c.txt").write_text("")
        result = TOOL_REGISTRY["glob"].execute(pattern="*.py", path=str(tmp_path))
        assert "a.py" in result.content
        assert "b.py" in result.content
        assert "c.txt" not in result.content

    def test_glob_recursive(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "deep.py").write_text("")
        result = TOOL_REGISTRY["glob"].execute(pattern="**/*.py", path=str(tmp_path))
        assert "deep.py" in result.content

    def test_glob_is_read_only(self):
        from nanocode.tools import TOOL_REGISTRY

        assert TOOL_REGISTRY["glob"].is_read_only is True


# === Test GrepTool ===


class TestGrepTool:
    def test_grep_finds_pattern(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        f = tmp_path / "code.py"
        f.write_text("def hello():\n    pass\ndef world():\n    pass\n")
        result = TOOL_REGISTRY["grep"].execute(pattern="def \\w+", path=str(tmp_path))
        assert "hello" in result.content
        assert "world" in result.content

    def test_grep_with_include(self, tmp_path):
        from nanocode.tools import TOOL_REGISTRY

        (tmp_path / "a.py").write_text("match here")
        (tmp_path / "b.txt").write_text("match here")
        result = TOOL_REGISTRY["grep"].execute(
            pattern="match", path=str(tmp_path), include="*.py"
        )
        assert "a.py" in result.content
        assert "b.txt" not in result.content

    def test_grep_is_read_only(self):
        from nanocode.tools import TOOL_REGISTRY

        assert TOOL_REGISTRY["grep"].is_read_only is True
