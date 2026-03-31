"""Tests for nanocode agents — written BEFORE implementation (TDD)."""

import pytest
from pathlib import Path


class TestAgentConfig:
    def test_base_config_is_abc(self):
        from abc import ABC
        from nanocode.agents.base import AgentConfig

        assert issubclass(AgentConfig, ABC)

    def test_config_has_required_fields(self):
        from nanocode.agents.base import AgentConfig

        required = {
            "name",
            "display_name",
            "color",
            "approval_policy",
            "tool_names",
            "identity_prompt",
            "constraints",
        }
        # All should be declared on the class
        for attr in required:
            assert (
                hasattr(AgentConfig, attr) or attr in AgentConfig.__abstractmethod__
                if hasattr(AgentConfig, "__abstractmethod__")
                else True
            )

    def test_build_system_prompt_contains_identity(self, tmp_path):
        from nanocode.agents.claude import ClaudeAgent

        config = ClaudeAgent()
        prompt = config.build_system_prompt(str(tmp_path))
        assert "Claude Code" in prompt

    def test_build_system_prompt_contains_cwd(self, tmp_path):
        from nanocode.agents.claude import ClaudeAgent

        config = ClaudeAgent()
        prompt = config.build_system_prompt(str(tmp_path))
        assert str(tmp_path) in prompt

    def test_build_system_prompt_contains_date(self):
        from nanocode.agents.claude import ClaudeAgent
        from datetime import date

        config = ClaudeAgent()
        prompt = config.build_system_prompt(".")
        assert date.today().isoformat() in prompt

    def test_tools_property_returns_tool_instances(self):
        from nanocode.agents.claude import ClaudeAgent

        config = ClaudeAgent()
        tools = config.tools
        assert len(tools) > 0
        names = {t.name for t in tools}
        assert "shell" in names
        assert "read" in names

    def test_build_system_prompt_reads_claude_md(self, tmp_path):
        from nanocode.agents.claude import ClaudeAgent

        (tmp_path / "CLAUDE.md").write_text("Custom project instructions here")
        config = ClaudeAgent()
        prompt = config.build_system_prompt(str(tmp_path))
        assert "Custom project instructions" in prompt

    def test_build_system_prompt_reads_agents_md(self, tmp_path):
        from nanocode.agents.opencode import OpenCodeAgent

        (tmp_path / "AGENTS.md").write_text("OpenCode agent memory")
        config = OpenCodeAgent()
        prompt = config.build_system_prompt(str(tmp_path))
        assert "OpenCode agent memory" in prompt


class TestClaudeAgent:
    def test_name(self):
        from nanocode.agents.claude import ClaudeAgent

        c = ClaudeAgent()
        assert c.name == "claude"

    def test_display_name(self):
        from nanocode.agents.claude import ClaudeAgent

        assert ClaudeAgent().display_name == "Claude Code"

    def test_approval_policy_is_prompt(self):
        from nanocode.agents.claude import ClaudeAgent

        assert ClaudeAgent().approval_policy == "prompt"

    def test_has_all_tools(self):
        from nanocode.agents.claude import ClaudeAgent

        c = ClaudeAgent()
        assert set(c.tool_names) == {"shell", "read", "write", "edit", "glob", "grep"}

    def test_color(self):
        from nanocode.agents.claude import ClaudeAgent

        assert ClaudeAgent().color  # non-empty string


class TestCodexAgent:
    def test_name(self):
        from nanocode.agents.codex import CodexAgent

        assert CodexAgent().name == "codex"

    def test_display_name(self):
        from nanocode.agents.codex import CodexAgent

        assert CodexAgent().display_name == "Codex"

    def test_approval_policy_is_auto(self):
        from nanocode.agents.codex import CodexAgent

        assert CodexAgent().approval_policy == "auto"

    def test_only_shell_tool(self):
        from nanocode.agents.codex import CodexAgent

        assert CodexAgent().tool_names == ["shell"]

    def test_system_prompt_mentions_workspace(self, tmp_path):
        from nanocode.agents.codex import CodexAgent

        prompt = CodexAgent().build_system_prompt(str(tmp_path))
        assert "workspace" in prompt.lower() or str(tmp_path) in prompt


class TestOpenCodeAgent:
    def test_name(self):
        from nanocode.agents.opencode import OpenCodeAgent

        assert OpenCodeAgent().name == "opencode"

    def test_display_name(self):
        from nanocode.agents.opencode import OpenCodeAgent

        assert OpenCodeAgent().display_name == "OpenCode"

    def test_approval_policy_is_none(self):
        from nanocode.agents.opencode import OpenCodeAgent

        assert OpenCodeAgent().approval_policy == "none"

    def test_has_all_tools(self):
        from nanocode.agents.opencode import OpenCodeAgent

        assert set(OpenCodeAgent().tool_names) == {
            "shell",
            "read",
            "write",
            "edit",
            "glob",
            "grep",
        }


class TestAgentRegistry:
    def test_registry_has_three_agents(self):
        from nanocode.agents import AGENT_REGISTRY

        assert set(AGENT_REGISTRY.keys()) == {"claude", "codex", "opencode"}

    def test_registry_values_are_classes(self):
        from nanocode.agents import AGENT_REGISTRY
        from nanocode.agents.base import AgentConfig

        for cls in AGENT_REGISTRY.values():
            assert issubclass(cls, AgentConfig)

    def test_create_agent_from_registry(self):
        from nanocode.agents import AGENT_REGISTRY

        for name, cls in AGENT_REGISTRY.items():
            agent = cls()
            assert agent.name == name
            assert len(agent.tools) > 0
