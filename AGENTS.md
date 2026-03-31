# AGENTS.md — NanoCode Development Guide

This guide helps agentic coding assistants understand how to work effectively in the NanoCode repository.

## Quick Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Verify installation
python -m nanocode --help
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_engine.py -v

# Run specific test
pytest tests/test_engine.py::test_engine_submit -v

# Run with coverage
pytest tests/ --cov=src/nanocode --cov-report=term-missing

# Run async tests (auto mode enabled in pyproject.toml)
pytest tests/test_engine.py -v -s
```

**Note**: All tests are async. The project uses `pytest-asyncio` with `asyncio_mode = "auto"`.

## Code Style Guidelines

### Imports

- Use `from __future__ import annotations` at the top of all modules for forward references
- Group imports: stdlib → third-party → local (nanocode)
- Use absolute imports: `from nanocode.tools import Tool`
- Lazy imports for optional dependencies (see `engine.py:57`)

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import AsyncIterator

from nanocode.agents.base import AgentConfig
from nanocode.tools import Tool
```

### Type Hints

- Use type hints for all function signatures
- Use `|` for union types (Python 3.10+): `str | None` instead of `Optional[str]`
- Use `Protocol` for structural typing (see `engine.py:45`)
- Use `@dataclass` for simple data structures (see `engine.py:15-39`)

```python
def create_backend(
    provider: str, *, api_key: str, base_url: str | None, model: str
) -> LLMBackend:
    ...

async def submit(self, user_input: str) -> AsyncIterator[Event]:
    ...
```

### Naming Conventions

- **Classes**: PascalCase (`ClaudeAgent`, `ShellTool`, `Engine`)
- **Functions/methods**: snake_case (`build_system_prompt`, `execute`)
- **Constants**: UPPER_SNAKE_CASE (`TOOL_REGISTRY`, `AGENT_REGISTRY`)
- **Private methods**: prefix with `_` (`_git_context`, `_classify`)
- **Agent names**: lowercase (`claude`, `codex`, `opencode`)

### Formatting

- Line length: No strict limit, but keep readable (typically < 100 chars)
- Use f-strings for formatting
- Docstrings: Module-level docstrings with `"""..."""` (see `engine.py:1`)
- Comments: Use `# ===` for section markers in core modules

```python
"""Core engine — event types, agent loop, backend factory. ★ CORE ★"""

# === Events ===
```

### Error Handling

- Use try/except for external operations (subprocess, file I/O)
- Return `ToolResult(content, is_error=True)` for tool errors
- Catch broad exceptions in subprocess calls (see `agents/base.py:64`)
- Use `subprocess.run(..., timeout=5)` for safety

```python
try:
    result = subprocess.run(["git", "branch"], capture_output=True, timeout=5)
    if result.returncode != 0:
        return ""
except Exception:
    return ""
```

## Project Structure

```
src/nanocode/
├── engine.py          # ★ Core: event types, agent loop, backend factory
├── router.py          # ★ Core: auto-routing logic
├── backends.py        # LLM backend implementations (OpenAI, Anthropic)
├── agents/
│   ├── base.py        # AgentConfig base class, system prompt builder
│   ├── claude.py      # Claude Code agent config
│   ├── codex.py       # Codex agent config
│   └── opencode.py    # OpenCode agent config
├── tools/
│   └── __init__.py    # Tool base class, registry, all tool implementations
├── ui/
│   ├── app.py         # Textual TUI main application
│   ├── chat_view.py   # Chat message list + input
│   ├── loading.py     # Greek mythology loading animations
│   ├── status_bar.py  # Agent status display
│   └── terminal_view.py # Tool output panel
└── history.py         # Conversation history persistence
```

## Key Patterns

### Adding a Tool

1. Subclass `Tool` in `tools/__init__.py`
2. Implement: `name`, `description`, `parameters`, `execute()`
3. Register in `TOOL_REGISTRY` dict
4. Add tests in `tests/test_tools.py`

```python
class MyTool(Tool):
    name = "my_tool"
    description = "Does something"
    parameters = {"type": "object", "properties": {...}}
    is_read_only = True
    
    def execute(self, **kwargs) -> ToolResult:
        try:
            # Implementation
            return ToolResult("success")
        except Exception as e:
            return ToolResult(str(e), is_error=True)

TOOL_REGISTRY["my_tool"] = MyTool()
```

### Adding an Agent

1. Create class in `agents/` inheriting from `AgentConfig`
2. Set: `name`, `display_name`, `color`, `approval_policy`, `tool_names`, `identity_prompt`
3. Register via `@register_agent` decorator
4. Add tests in `tests/test_agents.py`

### System Prompt Building

Agents automatically include:
- Identity prompt + constraints
- Current date and working directory
- Git branch (if in repo)
- `CLAUDE.md` and `AGENTS.md` files (if present)

See `agents/base.py:25-47` for implementation.

## Testing Patterns

- Use `pytest-asyncio` for async tests
- Mock external APIs with `pytest-mock`
- Test both success and error paths
- Use fixtures for common setup

```python
@pytest.mark.asyncio
async def test_engine_submit(mock_backend):
    engine = Engine(mock_backend)
    events = [e async for e in engine.submit("test")]
    assert any(isinstance(e, TextEvent) for e in events)
```

## Dependencies

- **openai**: OpenAI API client
- **anthropic**: Anthropic API client
- **textual**: Terminal UI framework
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities

## Notes for Agents

- Always read files before editing (Claude Code constraint)
- Use `glob` to find files before reading many files
- Test commands are in `pyproject.toml` under `[tool.pytest.ini_options]`
- The project uses async/await extensively — understand event loops
- System prompts are built dynamically from agent config + environment
- Tools return `ToolResult` objects with `content` and `is_error` fields
