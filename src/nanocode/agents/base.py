"""Agent base config — shared system prompt builder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

from nanocode.tools import Tool, get_tools


class AgentConfig(ABC):
    name: str
    display_name: str
    color: str
    approval_policy: str  # "prompt" | "auto" | "none"
    tool_names: list[str]
    identity_prompt: str
    constraints: list[str] = []

    @property
    def tools(self) -> list[Tool]:
        return get_tools(self.tool_names)

    def build_system_prompt(self, cwd: str) -> str:
        parts = [self.identity_prompt]
        parts.append(
            f"\n# Environment\nDate: {date.today().isoformat()}\nWorking directory: {cwd}"
        )

        # Git context
        git = self._git_context(cwd)
        if git:
            parts.append(f"\n# Git\n{git}")

        # Project memory files
        for fname in ("CLAUDE.md", "AGENTS.md"):
            p = Path(cwd) / fname
            if p.exists():
                parts.append(f"\n# {fname}\n{p.read_text().strip()}")

        if self.constraints:
            parts.append(
                "\n# Constraints\n" + "\n".join(f"- {c}" for c in self.constraints)
            )

        return "\n".join(parts)

    @staticmethod
    def _git_context(cwd: str) -> str:
        import subprocess

        try:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=5,
            )
            if branch.returncode != 0:
                return ""
            return f"Branch: {branch.stdout.strip()}"
        except Exception:
            return ""
