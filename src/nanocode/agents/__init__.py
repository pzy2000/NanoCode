"""Agent registry."""

from nanocode.agents.claude import ClaudeAgent
from nanocode.agents.codex import CodexAgent
from nanocode.agents.opencode import OpenCodeAgent

AGENT_REGISTRY: dict[str, type] = {
    "claude": ClaudeAgent,
    "codex": CodexAgent,
    "opencode": OpenCodeAgent,
}
