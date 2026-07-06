# Repository Guidelines

## Repository layout

This repository contains two independent Python example areas:

- `openai-agents-sdk/` contains OpenAI Responses API examples.
- `langgraph-agents/` contains the local Ollama-backed tweet generator and its own uv-managed project.
- `docs/` contains dated implementation and documentation change logs.

Do not assume both example areas share a virtual environment or dependency manifest.

## OpenAI examples

- Dependencies are listed in the root `requirements.txt`.
- `openai-agents-sdk/ai_config.py` loads the repository-level `.env` file.
- `OPENAI_API_KEY` is required and cannot be empty.
- `OPENAI_MODEL_NAME` is optional and defaults to `gpt-5-nano`.
- `SimpleClient` retains the last Responses API response ID for follow-up prompts.
- `BusinessIdeaInvestigator` performs a two-step investigation using the Responses API.
- Run scripts from `openai-agents-sdk/` so their local `ai_config` import resolves.

## LangGraph/Ollama project

- Manage dependencies from `langgraph-agents/` with uv and the checked-in `uv.lock`.
- Python 3.13 or newer is required by `langgraph-agents/pyproject.toml`.
- `langgraph-agents/tweet_generator/ollama_ai_config.py` is the canonical configuration and loads settings from the repository-level `.env` file.
- `langgraph-agents/ollama_ai_config.py` is a compatibility re-export for existing imports.
- `OLLAMA_MODEL_NAME` defaults to `lfm2.5-thinking:1.2b-q8_0`.
- `OLLAMA_BASE_URL` defaults to `http://localhost:11434`.
- The configured model must already be available to the target Ollama server.
- The current tweet generator uses a LangChain prompt/model runnable with `ChatOllama`; it does not yet construct a LangGraph graph.

## Tweet generator behavior

- Keep the generator in the importable `langgraph-agents/tweet_generator` package.
- `TweetGenerator` instances retain successful user and assistant messages, allowing later calls to refine previous tweets.
- Each call generates a draft, critiques it with the reflection chain, and generates a final revision.
- Reflection is internal: commit only the original request and final revision to conversation history.
- A successful call makes three sequential Ollama requests, which affects latency.
- Failed model calls must not be committed to conversation history.
- The configured Ollama model and base URL must both be passed to `ChatOllama`.
- Keep both supported launch modes functional from `langgraph-agents/`:

  - `uv run python tweet_generator/tweet_generator.py`
  - `uv run python -m tweet_generator.tweet_generator`

- Direct execution imports the adjacent configuration module; package execution uses its relative package import. Do not restore a runtime `sys.path` mutation.

## Development requirements

- Run Pyright on every changed Python file. Pyright is available in the LangGraph project's development dependency group.
- If Pyright is unavailable while changing Python, add it with `uv add --dev pyright` in the relevant uv project.
- Run `cargo check` after changing Rust files and fix all reported errors.
- When adding a feature, update `AGENTS.md` and any existing `CLAUDE.md`; create the applicable guidance file when neither exists.
- Preserve a Markdown change log under `docs/` for every task. Use a dated, descriptive filename so existing logs are never overwritten, and explain both the changes and their reasoning.
- Keep secrets and machine-specific values in `.env`; never commit them.

## Validation commands

Run LangGraph checks from `langgraph-agents/`:

```powershell
uv sync
uv run pyright ollama_ai_config.py tweet_generator/ollama_ai_config.py tweet_generator/tweet_generator.py tweet_generator/__init__.py
uv run python -c "from tweet_generator.tweet_generator import TweetGenerator; assert TweetGenerator is not None"
```

The last command validates imports without contacting Ollama. Running the tweet generator itself requires a reachable Ollama server and the configured model.
