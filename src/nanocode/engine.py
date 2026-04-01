"""Core engine — event types, agent loop, backend factory. ★ CORE ★"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from nanocode.agents.base import AgentConfig
from nanocode.tools import Tool, ToolResult


# === Events ===


@dataclass
class TextEvent:
    text: str


@dataclass
class ToolCallEvent:
    name: str
    args: dict
    call_id: str


@dataclass
class ToolResultEvent:
    name: str
    result: ToolResult
    call_id: str


@dataclass
class StatusEvent:
    status: str  # "thinking" | "done"


@dataclass
class UsageEvent:
    input_tokens: int
    output_tokens: int


Event = TextEvent | ToolCallEvent | ToolResultEvent | StatusEvent | UsageEvent


# === Backend Protocol ===


class LLMBackend(Protocol):
    def stream(
        self, system: str, messages: list, tools: list[Tool]
    ) -> AsyncIterator[Event]: ...


# === Factory ===


def create_backend(
    provider: str, *, api_key: str, base_url: str | None, model: str
) -> LLMBackend:
    from nanocode.backends import OpenAIBackend, AnthropicBackend

    if provider == "anthropic":
        return AnthropicBackend(api_key=api_key, base_url=base_url, model=model)
    return OpenAIBackend(api_key=api_key, base_url=base_url, model=model)


# === Engine ===


class Engine:
    def __init__(self, backend: LLMBackend):
        self.backend = backend
        self.messages: list[dict] = []
        self.tools: dict[str, Tool] = {}
        self.system_prompt: str = ""
        self.approval_policy: str = "none"
        self.max_iterations: int = 64

    def configure(self, config: AgentConfig, cwd: str = ".") -> None:
        self.system_prompt = config.build_system_prompt(cwd)
        self.tools = {t.name: t for t in config.tools}
        self.approval_policy = config.approval_policy

    def configure_tools(self, tools: dict[str, Tool]) -> None:
        self.tools = tools

    def get_model(self) -> str:
        return getattr(self.backend, "model", "")

    def set_model(self, model: str) -> None:
        self.backend.model = model

    async def submit(self, user_input: str) -> AsyncIterator[Event]:
        self.messages.append({"role": "user", "content": user_input})
        for _ in range(self.max_iterations):
            yield StatusEvent("thinking")
            text_buf = ""
            tool_calls: list[ToolCallEvent] = []
            async for event in self.backend.stream(
                self.system_prompt, self.messages, list(self.tools.values())
            ):
                if isinstance(event, TextEvent):
                    text_buf += event.text
                    yield event
                elif isinstance(event, ToolCallEvent):
                    tool_calls.append(event)
                elif isinstance(event, UsageEvent):
                    yield event
            assistant_msg: dict = {"role": "assistant", "content": text_buf}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {"id": tc.call_id, "name": tc.name, "args": tc.args}
                    for tc in tool_calls
                ]
            self.messages.append(assistant_msg)
            if not tool_calls:
                yield StatusEvent("done")
                break
            for tc in tool_calls:
                yield tc
                tool = self.tools.get(tc.name)
                result = (
                    tool.execute(**tc.args)
                    if tool
                    else ToolResult(f"Unknown tool: {tc.name}", is_error=True)
                )
                yield ToolResultEvent(name=tc.name, result=result, call_id=tc.call_id)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.call_id,
                        "content": result.content,
                    }
                )

    async def compact(self) -> str:
        """Summarize conversation history and replace messages with the summary."""
        if not self.messages:
            history_text = "(empty conversation)"
        else:
            history_text = "\n".join(
                f"{m['role']}: {m.get('content', '')}"
                for m in self.messages
                if m.get("content")
            )
        prompt = (
            "Please summarize the following conversation into a concise context summary, "
            "preserving key decisions, code changes, and important context. "
            "Reply in the same language as the conversation.\n\n"
            + history_text
        )
        summary = ""
        async for event in self.backend.stream(
            "You are a helpful assistant that summarizes conversations concisely.",
            [{"role": "user", "content": prompt}],
            [],
        ):
            if isinstance(event, TextEvent):
                summary += event.text
        self.messages = [
            {"role": "user", "content": f"[Conversation Summary]\n{summary}"},
            {"role": "assistant", "content": "Understood, I will continue from this context."},
        ]
        return summary
