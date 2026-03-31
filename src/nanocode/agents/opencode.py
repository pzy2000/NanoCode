"""OpenCode style agent config."""

from nanocode.agents.base import AgentConfig


class OpenCodeAgent(AgentConfig):
    name = "opencode"
    display_name = "OpenCode"
    color = "#61AFEF"
    approval_policy = "none"
    tool_names = ["shell", "read", "write", "edit", "glob", "grep"]
    identity_prompt = (
        "You are OpenCode, an open-source coding agent.\n"
        "You help with complex software engineering tasks including multi-file refactoring,\n"
        "project scaffolding, and thorough code analysis.\n"
        "You execute tools automatically without requiring approval.\n"
        "Be thorough and systematic in your approach."
    )
    constraints = [
        "Be thorough — explore before making changes",
        "Use task decomposition for complex requests",
    ]
