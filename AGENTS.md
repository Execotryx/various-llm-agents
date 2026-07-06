# Repository Guidelines

## LangGraph Ollama configuration

- Use `langgraph-agents/ollama_ai_config.py` for local Ollama connection settings.
- Configure the model with `OLLAMA_MODEL_NAME`; the default is `lfm2.5-thinking:1.2b-q8_0`.
- Configure the server with `OLLAMA_BASE_URL`; the default is `http://localhost:11434`.
- Keep secrets and machine-specific settings in the repository-level `.env` file.

## Tweet generator

- Keep the generator in the importable `langgraph-agents/tweet_generator` package.
- Run or import package modules from the `langgraph-agents` project directory.
- Keep direct execution of `tweet_generator.py` functional for IDE run commands.
- Preserve request and response messages on each `TweetGenerator` instance so feedback can refine earlier output.

## Validation

- Run Pyright on every changed Python file.
- Record feature changes and their rationale in a dated Markdown file under `docs/`.
