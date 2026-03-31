"""Tool base classes, registry, and all tool implementations."""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# === Base ===


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


class Tool(ABC):
    name: str
    description: str
    parameters: dict
    is_read_only: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_anthropic_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


# === Shell ===


class ShellTool(Tool):
    name = "shell"
    description = "Execute a shell command. Returns stdout+stderr."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run"},
            "workdir": {"type": "string", "description": "Optional working directory"},
        },
        "required": ["command"],
    }

    def execute(self, *, command: str, workdir: str | None = None, **kw) -> ToolResult:
        try:
            r = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=workdir,
            )
            output = (r.stdout + r.stderr).strip()
            return ToolResult(output or "(no output)", is_error=r.returncode != 0)
        except Exception as e:
            return ToolResult(str(e), is_error=True)


# === File Read ===


class FileReadTool(Tool):
    name = "read"
    description = "Read a file with line numbers. Supports offset and limit."
    is_read_only = True
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "offset": {"type": "integer", "description": "1-indexed start line"},
            "limit": {"type": "integer", "description": "Max lines to read"},
        },
        "required": ["file_path"],
    }

    def execute(
        self, *, file_path: str, offset: int = 1, limit: int = 2000, **kw
    ) -> ToolResult:
        try:
            lines = Path(file_path).read_text().splitlines()
            start = max(0, offset - 1)
            selected = lines[start : start + limit]
            numbered = [f"{start + i + 1}: {line}" for i, line in enumerate(selected)]
            return ToolResult("\n".join(numbered))
        except Exception as e:
            return ToolResult(str(e), is_error=True)


# === File Write ===


class FileWriteTool(Tool):
    name = "write"
    description = "Write content to a file. Creates parent directories."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["file_path", "content"],
    }

    def execute(self, *, file_path: str, content: str, **kw) -> ToolResult:
        try:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return ToolResult(f"Wrote {len(content)} bytes to {file_path}")
        except Exception as e:
            return ToolResult(str(e), is_error=True)


# === File Edit ===


class FileEditTool(Tool):
    name = "edit"
    description = "Replace an exact string in a file."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "old_string": {"type": "string"},
            "new_string": {"type": "string"},
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def execute(
        self, *, file_path: str, old_string: str, new_string: str, **kw
    ) -> ToolResult:
        try:
            p = Path(file_path)
            text = p.read_text()
            if old_string not in text:
                return ToolResult("old_string not found in file", is_error=True)
            text = text.replace(old_string, new_string, 1)
            p.write_text(text)
            return ToolResult(f"Edited {file_path}")
        except Exception as e:
            return ToolResult(str(e), is_error=True)


# === Glob ===


class GlobTool(Tool):
    name = "glob"
    description = "Find files matching a glob pattern."
    is_read_only = True
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string", "description": "Directory to search in"},
        },
        "required": ["pattern"],
    }

    def execute(self, *, pattern: str, path: str = ".", **kw) -> ToolResult:
        try:
            matches = sorted(Path(path).glob(pattern))
            if not matches:
                return ToolResult("No matches found")
            return ToolResult("\n".join(str(m) for m in matches))
        except Exception as e:
            return ToolResult(str(e), is_error=True)


# === Grep ===


class GrepTool(Tool):
    name = "grep"
    description = "Search file contents with regex. Returns matching lines."
    is_read_only = True
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern"},
            "path": {"type": "string", "description": "Directory to search"},
            "include": {
                "type": "string",
                "description": "File glob filter, e.g. '*.py'",
            },
        },
        "required": ["pattern"],
    }

    def execute(
        self, *, pattern: str, path: str = ".", include: str | None = None, **kw
    ) -> ToolResult:
        try:
            regex = re.compile(pattern)
            results = []
            root = Path(path)
            for fpath in sorted(root.rglob("*")):
                if not fpath.is_file():
                    continue
                if include and not fnmatch.fnmatch(fpath.name, include):
                    continue
                try:
                    for i, line in enumerate(fpath.read_text().splitlines(), 1):
                        if regex.search(line):
                            results.append(f"{fpath}:{i}: {line.strip()}")
                except (UnicodeDecodeError, PermissionError):
                    continue
            return ToolResult("\n".join(results) if results else "No matches found")
        except Exception as e:
            return ToolResult(str(e), is_error=True)


# === Registry ===

TOOL_REGISTRY: dict[str, Tool] = {
    "shell": ShellTool(),
    "read": FileReadTool(),
    "write": FileWriteTool(),
    "edit": FileEditTool(),
    "glob": GlobTool(),
    "grep": GrepTool(),
}


def get_tools(names: list[str]) -> list[Tool]:
    return [TOOL_REGISTRY[n] for n in names if n in TOOL_REGISTRY]
