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
- The tweet generator compiles a LangGraph `StateGraph` with explicit replacement state around LangChain generation, reflection, and revision runnables.

## Tweet generator behavior

- Keep the generator in the importable `langgraph-agents/tweet_generator` package.
- `TweetGeneratorSettings` controls reflection rounds, bounded history, and model temperature. Keep its defaults at one round, four history turns, and `0.7` unless requirements change.
- `TweetGenerator` instances retain a bounded deque of complete successful request/response turns. Never retain half a turn or mutate history after a failed call.
- Keep the graph topology as `START -> generate_draft -> conditional(reflect | END)`, then `reflect -> revise -> conditional(reflect | END)` unless workflow requirements change.
- A call must make exactly `1 + (2 * reflection_rounds)` model requests.
- Keep history, current request, current draft, latest critique, and reflection counters in explicit graph fields. Drafts and critiques replace their fields rather than accumulating messages.
- Reflection receives only the current request and latest draft. Revision receives only the current request, latest draft, and latest critique. Do not restore role reversal.
- StateGraph nodes must accept `TweetState` and return partial state updates.
- Reflection is internal: commit only the original request and final revision to conversation history.
- The default single reflection round makes three sequential Ollama requests.
- Failed model calls must not be committed to conversation history.
- Runtime components are cached for up to eight model name, base URL, and temperature combinations, but conversation history remains per generator instance. Shared runtime invocation is serialized as a conservative compatibility fallback for clients without concurrency guarantees.
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
uv run python -m unittest discover -s tests -v
uv run python -c "from tweet_generator.tweet_generator import TweetGenerator; assert TweetGenerator is not None"
```

The last command validates imports without contacting Ollama. Running the tweet generator itself requires a reachable Ollama server and the configured model.
