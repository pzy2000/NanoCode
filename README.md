# nanocode

A micro coding agent that auto-routes between Claude Code, Codex, and OpenCode styles. **193 lines of core logic**, dual-backend support (OpenAI + Anthropic), and Greek mythology-themed loading animations.

![Tests](https://img.shields.io/badge/tests-95%2F95%20passing-brightgreen)
![Code Size](https://img.shields.io/badge/core%20logic-193%20lines-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **Auto-routing Agent**: LLM automatically selects the best agent (Claude/Codex/OpenCode) for your task
- **Manual Agent Switching**: Use `/agent claude|codex|opencode|auto` to switch on the fly
- **Dual Backend Support**: Works with OpenAI-compatible APIs and Anthropic natively
- **Minimal Core**: Only 193 lines of core scheduling logic (engine + router)
- **Full TUI**: Textual-based terminal UI with real-time streaming, tool output, and status bar
- **Greek Mythology Loading**: "Consulting the Oracle at Delphi...", "Weaving code with Athena..." 🏛️
- **100% Test Coverage**: 95 tests, TDD-driven development

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key OR Anthropic API key

### Installation

```bash
git clone https://github.com/yourusername/nanocode.git
cd nanocode
pip install -e .
```

### Run

```bash
# Using OpenAI-compatible API (default)
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1  # optional
nanocode

# Using Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
nanocode --provider anthropic

# Using local LLM (e.g., Ollama)
export OPENAI_API_KEY=dummy
export OPENAI_BASE_URL=http://localhost:8000/v1
nanocode
```

## 📖 Usage

### Interactive Commands

| Command | Effect |
|---------|--------|
| `/agent claude` | Switch to Claude Code style (careful, multi-step reasoning) |
| `/agent codex` | Switch to Codex style (quick shell commands, direct generation) |
| `/agent opencode` | Switch to OpenCode style (complex refactoring, multi-file changes) |
| `/agent auto` | Enable auto-routing (LLM decides best agent per request) |
| `/agent` | Show current mode and available agents |
| `/clear` | Clear conversation history |
| `/exit` | Quit |
| `Ctrl+C` | Quit |

### Example Session

```
> /agent auto
Mode: auto (active: none). Available: auto, claude, codex, opencode

> write a python function to calculate fibonacci
⚡ Claude Code ⚡auto
Consulting the Oracle at Delphi...
[AI generates code with careful explanation]

> now optimize it for performance
⚡ Codex ⚡auto
Hermes is delivering...
[AI generates optimized shell commands and code]

> refactor this across multiple files
⚡ OpenCode ⚡auto
Athena reviews the strategy...
[AI performs complex multi-file refactoring]
```

## 🏗️ Architecture

### Core Components (193 lines)

```
engine.py (123 lines)
  ├─ Event types (TextEvent, ToolCallEvent, ToolResultEvent, StatusEvent)
  ├─ LLMBackend protocol
  ├─ Engine class (agent loop, tool execution, message history)
  └─ create_backend() factory

router.py (70 lines)
  ├─ Router class (manual + auto routing)
  ├─ /agent command handler
  └─ LLM-based agent classification
```

### Supporting Modules

```
backends.py (120 lines)
  ├─ OpenAIBackend (streaming, tool call buffering)
  └─ AnthropicBackend (message format conversion)

agents/ (136 lines)
  ├─ base.py: AgentConfig + SystemPromptBuilder
  ├─ claude.py: Claude Code configuration
  ├─ codex.py: Codex configuration
  └─ opencode.py: OpenCode configuration

tools/ (225 lines)
  ├─ Tool ABC + ToolResult
  ├─ 6 tools: shell, read, write, edit, glob, grep
  └─ TOOL_REGISTRY

ui/ (438 lines)
  ├─ app.py: Textual TUI main app
  ├─ chat_view.py: Message list + input
  ├─ loading.py: Greek mythology animations
  ├─ status_bar.py: Agent status display
  └─ terminal_view.py: Tool output panel
```

**Total: 905 lines** (including tests: 1,043 lines)

## 🧠 Agent Styles

### Claude Code
- **Approval Policy**: Prompt (asks before write/shell operations)
- **Tools**: All 6 (shell, read, write, edit, glob, grep)
- **Style**: Careful, multi-step reasoning; reads before editing
- **Best For**: Code review, debugging, complex refactoring

### Codex
- **Approval Policy**: Auto (executes without asking)
- **Tools**: Shell only
- **Style**: Direct, quick; one command at a time
- **Best For**: Quick code generation, build/test/deploy tasks

### OpenCode
- **Approval Policy**: None (fully autonomous)
- **Tools**: All 6 (shell, read, write, edit, glob, grep)
- **Style**: Thorough, systematic; explores before changing
- **Best For**: Complex multi-file refactoring, project scaffolding

## 🔄 Auto-Routing

When in `auto` mode, nanocode sends a lightweight LLM call to classify your request:

```
User: "write a python function to calculate fibonacci"
↓
Router: "This is code generation → codex"
↓
Engine: Switches to Codex config (shell-only, auto-approve)
↓
AI: Generates code directly
```

Classification is fast (max_tokens=10) and cached per agent switch.

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_engine.py -v
pytest tests/test_tools.py -v
pytest tests/test_agents.py -v
pytest tests/test_router.py -v
pytest tests/test_ui.py -v

# Coverage
pytest tests/ --cov=src/nanocode
```

**95 tests, 100% passing** — TDD-driven development ensures reliability.

## 🛠️ Development

### Project Structure

```
nanocode/
├── pyproject.toml          # Build config
├── README.md               # This file
├── src/nanocode/           # Source code
│   ├── __main__.py         # Entry point
│   ├── engine.py           # ★ Core agent loop
│   ├── router.py           # ★ Auto-routing
│   ├── backends.py         # LLM backends
│   ├── agents/             # Agent configs
│   ├── tools/              # Tool implementations
│   └── ui/                 # Textual TUI
└── tests/                  # Test suite (95 tests)
```

### Adding a New Tool

1. Create a class inheriting from `Tool` in `tools/__init__.py`
2. Implement `name`, `description`, `parameters`, `execute()`
3. Register in `TOOL_REGISTRY`
4. Add tests in `tests/test_tools.py`

Example:

```python
class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {"type": "object", "properties": {...}}
    is_read_only = False

    def execute(self, **kwargs) -> ToolResult:
        # Implementation
        return ToolResult("success")

TOOL_REGISTRY["my_tool"] = MyTool()
```

### Adding a New Agent

1. Create a class inheriting from `AgentConfig` in `agents/`
2. Set `name`, `display_name`, `color`, `approval_policy`, `tool_names`, `identity_prompt`, `constraints`
3. Register in `AGENT_REGISTRY` via `@register_agent` decorator
4. Add tests in `tests/test_agents.py`

## 🎨 UI Features

- **Real-time Streaming**: See AI responses character-by-character
- **Tool Visualization**: Tool calls and results displayed in terminal panel
- **Agent Status Bar**: Shows current agent name, color, and routing mode
- **Greek Mythology Loading**: 12 thinking phrases + 6 tool phrases
- **Syntax Highlighting**: Code blocks highlighted by language
- **Message History**: Scrollable chat with user/AI/system messages

## 🔌 Extensibility

### Custom Backend

Implement the `LLMBackend` protocol:

```python
class MyBackend:
    def stream(self, system: str, messages: list, tools: list[Tool]) -> AsyncIterator[Event]:
        # Yield TextEvent, ToolCallEvent, etc.
        ...
```

Register in `create_backend()` factory.

### Custom Agent

Subclass `AgentConfig` and register:

```python
@register_agent("my_agent")
class MyAgent(AgentConfig):
    name = "my_agent"
    # ... configuration
```

## 📊 Performance

- **Startup**: < 1s
- **First LLM Call**: Depends on backend (typically 1-3s)
- **Streaming**: Real-time token-by-token display
- **Memory**: ~50MB baseline (grows with conversation history)

## 🐛 Troubleshooting

### "No running event loop" error
- Ensure you're running `nanocode` from the command line, not in a Jupyter notebook
- Use `conda activate nano && nanocode` if using conda

### "Unknown tool" error
- Check that the tool is registered in `TOOL_REGISTRY`
- Verify the agent config includes the tool in `tool_names`

### API connection errors
- Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
- Check `OPENAI_BASE_URL` or `ANTHROPIC_BASE_URL` if using custom endpoints
- Test connectivity: `curl http://localhost:8000/v1/models` (for local LLM)

## 📝 License

MIT License — see LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for new functionality (TDD)
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## 🙏 Acknowledgments

- Inspired by Claude Code, Codex, and OpenCode
- Built with [Textual](https://textual.textualize.io/) for TUI
- Powered by [OpenAI](https://openai.com/) and [Anthropic](https://www.anthropic.com/)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/nanocode/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/nanocode/discussions)
- **Email**: your-email@example.com

---

**Made with ❤️ and 193 lines of core logic**
