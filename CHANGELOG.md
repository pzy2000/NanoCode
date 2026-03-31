# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-03-31

### Added

- **Core Engine** (123 lines): Agent loop with streaming support, tool execution, message history management
- **Auto-Routing Router** (70 lines): LLM-based agent classification + manual `/agent` command switching
- **Dual Backend Support**: OpenAI-compatible APIs and Anthropic native support
- **Three Agent Styles**:
  - Claude Code: Careful, multi-step reasoning with approval gates
  - Codex: Quick, direct code generation with auto-approval
  - OpenCode: Complex refactoring with full autonomy
- **Six Built-in Tools**: shell, read, write, edit, glob, grep
- **Full Textual TUI**: Real-time streaming, tool visualization, Greek mythology loading animations
- **Comprehensive Test Suite**: 95 tests covering all core functionality (TDD-driven)
- **Documentation**: README, CONTRIBUTING, LICENSE, this CHANGELOG

### Features

- Real-time token-by-token streaming from LLM
- Tool call buffering and execution with error handling
- Conversation history management
- Agent configuration system with dynamic switching
- Greek mythology-themed loading phrases (12 thinking + 6 tool phrases)
- Status bar showing current agent, routing mode, and loading state
- Terminal panel for tool output visualization
- Chat view with markdown rendering
- Support for local LLMs via OpenAI-compatible endpoints

### Technical Highlights

- **Minimal Core**: 193 lines of core scheduling logic (engine + router)
- **TDD-Driven**: 95 tests, 100% passing
- **Clean Architecture**: Modular design with clear separation of concerns
- **Type-Safe**: Full type hints throughout
- **Async-First**: Async/await for responsive UI
- **Zero External Frameworks**: No LangChain, no complex dependencies

### Known Limitations

- Single conversation per session (no multi-session support yet)
- No persistent conversation storage
- Limited to text-based interactions (no image support yet)
- Auto-routing requires LLM API call (adds ~1s latency)

---

## Future Roadmap

### v0.2.0 (Planned)

- [ ] Persistent conversation storage
- [ ] Multi-session support
- [ ] Image input support
- [ ] Custom tool registration via plugins
- [ ] Web UI alternative to TUI
- [ ] Conversation export (JSON, Markdown)

### v0.3.0 (Planned)

- [ ] MCP (Model Context Protocol) support
- [ ] Advanced reasoning modes (chain-of-thought, tree-of-thought)
- [ ] Batch processing
- [ ] API server mode
- [ ] Performance optimizations

---

## Migration Guide

### From v0.0.0 to v0.1.0

This is the initial release. No migration needed.

---

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
