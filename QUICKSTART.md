# Quick Start Guide

Get nanocode running in 5 minutes.

## 1. Install

```bash
git clone https://github.com/yourusername/nanocode.git
cd nanocode
pip install -e .
```

## 2. Set API Key

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# OR Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# OR Local LLM (Ollama, vLLM, etc.)
export OPENAI_API_KEY=dummy
export OPENAI_BASE_URL=http://localhost:8000/v1
```

## 3. Run

```bash
nanocode
```

## 4. Try Commands

```
> write a python function to calculate fibonacci
> /agent codex
> /agent auto
> /clear
> /exit
```

## Common Issues

**"No module named nanocode"**
- Run `pip install -e .` from the nanocode directory

**"API key not found"**
- Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable

**"Connection refused"**
- Check your `OPENAI_BASE_URL` or local LLM is running

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Review [CHANGELOG.md](CHANGELOG.md) for version history
