"""LLM backend implementations — OpenAI and Anthropic."""

from __future__ import annotations

import json
from typing import AsyncIterator

import anthropic
import openai

from nanocode.tools import Tool

# Import event types (will be defined in engine.py)
from nanocode.engine import TextEvent, ToolCallEvent, Event


class OpenAIBackend:
    def __init__(self, api_key: str, base_url: str | None, model: str):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def stream(
        self, system: str, messages: list, tools: list[Tool]
    ) -> AsyncIterator[Event]:
        api_messages = [{"role": "system", "content": system}] + self._convert(messages)
        tool_defs = [t.to_openai_schema() for t in tools] or None
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            tools=tool_defs,
            stream=True,
        )
        tc_buf: dict[int, dict] = {}
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue
            if delta.content:
                yield TextEvent(delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    buf = tc_buf.setdefault(
                        tc.index, {"id": "", "name": "", "arguments": ""}
                    )
                    if tc.id:
                        buf["id"] = tc.id
                    if tc.function and tc.function.name:
                        buf["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        buf["arguments"] += tc.function.arguments
        for idx in sorted(tc_buf):
            tc = tc_buf[idx]
            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            yield ToolCallEvent(name=tc["name"], args=args, call_id=tc["id"])

    @staticmethod
    def _convert(messages: list[dict]) -> list[dict]:
        """Convert internal message format to OpenAI API format."""
        result = []
        for m in messages:
            if m["role"] == "assistant" and "tool_calls" in m:
                # Convert internal tool_calls to OpenAI format
                result.append(
                    {
                        "role": "assistant",
                        "content": m.get("content") or None,
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"]),
                                },
                            }
                            for tc in m["tool_calls"]
                        ],
                    }
                )
            else:
                result.append(m)
        return result


class AnthropicBackend:
    def __init__(self, api_key: str, base_url: str | None, model: str):
        kw = {"api_key": api_key}
        if base_url:
            kw["base_url"] = base_url
        self.client = anthropic.AsyncAnthropic(**kw)
        self.model = model

    async def stream(
        self, system: str, messages: list, tools: list[Tool]
    ) -> AsyncIterator[Event]:
        tool_defs = [t.to_anthropic_schema() for t in tools] or None
        api_msgs = self._convert(messages)
        kw = dict(model=self.model, max_tokens=8192, system=system, messages=api_msgs)
        if tool_defs:
            kw["tools"] = tool_defs
        async with self.client.messages.stream(**kw) as stream:
            async for event in stream:
                if (
                    event.type == "content_block_delta"
                    and event.delta.type == "text_delta"
                ):
                    yield TextEvent(event.delta.text)
            final = await stream.get_final_message()
            for block in final.content:
                if block.type == "tool_use":
                    yield ToolCallEvent(
                        name=block.name, args=block.input, call_id=block.id
                    )

    @staticmethod
    def _convert(messages: list[dict]) -> list[dict]:
        result = []
        for m in messages:
            if m["role"] == "tool":
                result.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": m["tool_call_id"],
                                "content": m["content"],
                            }
                        ],
                    }
                )
            elif m["role"] == "assistant" and "tool_calls" in m:
                content = (
                    [{"type": "text", "text": m["content"]}] if m.get("content") else []
                )
                content += [
                    {
                        "type": "tool_use",
                        "id": t["id"],
                        "name": t["name"],
                        "input": t["args"],
                    }
                    for t in m["tool_calls"]
                ]
                result.append({"role": "assistant", "content": content})
            else:
                result.append(m)
        return result
