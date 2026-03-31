"""Router — auto-routing + /agent command. ★ CORE ★"""

from __future__ import annotations
from nanocode.agents import AGENT_REGISTRY
from nanocode.agents.base import AgentConfig
from nanocode.engine import Engine

ROUTER_PROMPT = """Classify this coding request into exactly one agent name.
- "claude": explanation, debugging, code review, careful multi-step reasoning
- "codex": direct code generation, quick shell commands, build/test/deploy
- "opencode": complex refactoring, multi-file changes, project scaffolding
Reply with ONLY the agent name, nothing else."""


class Router:
    def __init__(self, engine: Engine, cwd: str = "."):
        self.engine, self.cwd = engine, cwd
        self.mode: str = "auto"
        self.current_agent: AgentConfig | None = None

    def _apply(self, name: str) -> AgentConfig:
        if self.current_agent and self.current_agent.name == name:
            return self.current_agent
        config = AGENT_REGISTRY[name]()
        self.engine.configure(config, cwd=self.cwd)
        self.current_agent = config
        return config

    def handle_command(self, text: str) -> str | None:
        if not text.startswith("/agent"):
            return None
        parts = text.split()
        if len(parts) < 2:
            cur = self.current_agent.display_name if self.current_agent else "none"
            return f"Mode: {self.mode} (active: {cur}). Available: auto, {', '.join(AGENT_REGISTRY)}"
        name = parts[1].lower()
        if name == "auto":
            self.mode = "auto"
            return "Switched to auto routing"
        if name not in AGENT_REGISTRY:
            return (
                f"Unknown agent: {name}. Available: auto, {', '.join(AGENT_REGISTRY)}"
            )
        self.mode = name
        cfg = self._apply(name)
        return f"Switched to {cfg.display_name}"

    async def resolve(self, user_input: str) -> AgentConfig:
        target = self.mode if self.mode != "auto" else await self._classify(user_input)
        if target not in AGENT_REGISTRY:
            target = "claude"
        return self._apply(target)

    async def _classify(self, user_input: str) -> str:
        try:
            if hasattr(self.engine.backend, "client"):
                resp = await self.engine.backend.client.chat.completions.create(
                    model=self.engine.backend.model,
                    max_tokens=10,
                    messages=[
                        {"role": "system", "content": ROUTER_PROMPT},
                        {"role": "user", "content": user_input},
                    ],
                )
                choice = resp.choices[0].message.content.strip().lower()
                if choice in AGENT_REGISTRY:
                    return choice
        except Exception:
            pass
        return "claude"
