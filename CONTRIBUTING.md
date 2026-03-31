# Contributing to nanocode

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- A code editor (VS Code, PyCharm, etc.)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/nanocode.git
cd nanocode

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/ -v
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-feature
# or for bug fixes:
git checkout -b fix/my-bug
```

### 2. Follow TDD (Test-Driven Development)

nanocode is built with TDD. For any new feature:

1. **Write tests first** in `tests/test_*.py`
2. **Run tests** to see them fail: `pytest tests/test_*.py -v`
3. **Implement the feature** in `src/nanocode/`
4. **Run tests** to see them pass
5. **Refactor** if needed while keeping tests green

### 3. Code Style

- Follow PEP 8
- Use type hints for function signatures
- Keep functions small and focused
- Add docstrings to public functions

Example:

```python
def my_function(input_str: str) -> str:
    """Process input string and return result.
    
    Args:
        input_str: The input string to process
        
    Returns:
        The processed string
    """
    return input_str.upper()
```

### 4. Commit Messages

Use clear, descriptive commit messages:

```
feat: add new tool for file compression
fix: resolve CSS selector issue in TUI
docs: update README with new examples
test: add tests for router classification
refactor: simplify engine loop logic
```

Format: `<type>: <description>`

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

### 5. Run Tests Before Pushing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_engine.py -v

# Run with coverage
pytest tests/ --cov=src/nanocode
```

All tests must pass before submitting a PR.

## Adding a New Tool

1. Create a test in `tests/test_tools.py`:

```python
class TestMyTool:
    def test_my_tool_works(self):
        from nanocode.tools import TOOL_REGISTRY
        result = TOOL_REGISTRY["my_tool"].execute(arg="value")
        assert result.content == "expected"
```

2. Implement in `src/nanocode/tools/__init__.py`:

```python
class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "arg": {"type": "string"}
        },
        "required": ["arg"]
    }
    is_read_only = False

    def execute(self, *, arg: str, **kw) -> ToolResult:
        try:
            result = do_something(arg)
            return ToolResult(result)
        except Exception as e:
            return ToolResult(str(e), is_error=True)

TOOL_REGISTRY["my_tool"] = MyTool()
```

3. Add to agent configs if needed in `src/nanocode/agents/*.py`

## Adding a New Agent

1. Create a test in `tests/test_agents.py`:

```python
class TestMyAgent:
    def test_my_agent_exists(self):
        from nanocode.agents import AGENT_REGISTRY
        assert "my_agent" in AGENT_REGISTRY
```

2. Create `src/nanocode/agents/my_agent.py`:

```python
from nanocode.agents.base import AgentConfig

class MyAgent(AgentConfig):
    name = "my_agent"
    display_name = "My Agent"
    color = "#FF0000"
    approval_policy = "prompt"
    tool_names = ["shell", "read", "write"]
    identity_prompt = "You are My Agent..."
    constraints = ["Be careful", "Always verify"]
```

3. Register in `src/nanocode/agents/__init__.py`:

```python
from nanocode.agents.my_agent import MyAgent

AGENT_REGISTRY: dict[str, type] = {
    # ... existing agents
    "my_agent": MyAgent,
}
```

## Submitting a Pull Request

1. Push your branch: `git push origin feature/my-feature`
2. Open a PR on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to any related issues (#123)
   - Confirmation that tests pass

3. Address review feedback
4. Maintainers will merge when approved

## Project Structure

```
nanocode/
├── src/nanocode/
│   ├── engine.py          # Core agent loop
│   ├── router.py          # Auto-routing logic
│   ├── backends.py        # LLM backends
│   ├── agents/            # Agent configurations
│   ├── tools/             # Tool implementations
│   └── ui/                # TUI components
├── tests/                 # Test suite
├── pyproject.toml         # Build configuration
├── README.md              # Project documentation
└── CONTRIBUTING.md        # This file
```

## Key Concepts

### Engine Loop

The core agent loop in `engine.py`:

1. User submits input
2. Engine sends to LLM with system prompt + tools
3. LLM streams response (text + tool calls)
4. Engine executes tools
5. Results appended to history
6. Loop continues until no more tool calls

### Router

The router in `router.py` handles:

- Manual agent switching via `/agent` command
- Auto-routing via LLM classification
- Agent configuration management

### Tools

Tools are defined in `tools/__init__.py`:

- Inherit from `Tool` ABC
- Implement `execute(**kwargs) -> ToolResult`
- Register in `TOOL_REGISTRY`
- Can be read-only or write-enabled

## Performance Considerations

- Keep tool execution fast (< 1s ideally)
- Minimize LLM calls in hot paths
- Cache agent configurations
- Stream responses for better UX

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions
- Update CHANGELOG.md with notable changes
- Add comments for complex logic

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before opening new ones

---

Thank you for contributing to nanocode! 🎉
