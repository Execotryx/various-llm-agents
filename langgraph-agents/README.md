# Local Ollama tweet generator

This project generates and iteratively refines tweets with a locally hosted Ollama model. It uses LangChain's `ChatOllama` and prompt templates inside a LangGraph `StateGraph` reflection workflow.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- A running Ollama server
- The configured Ollama model installed on that server

Install the locked Python dependencies from this directory:

```powershell
uv sync
```

The default model is `lfm2.5-thinking:1.2b-q8_0`. Install it in Ollama before running the example, or select another installed model through the environment configuration.

## Configuration

Create `.env` in the repository root, one directory above this project:

```dotenv
OLLAMA_MODEL_NAME=lfm2.5-thinking:1.2b-q8_0
OLLAMA_BASE_URL=http://localhost:11434
```

Both settings are optional. The canonical `tweet_generator/ollama_ai_config.py` module uses the values shown above as defaults, rejects empty values, trims surrounding whitespace, and removes a trailing slash from the base URL. The root `ollama_ai_config.py` remains as a compatibility import.

## Run the example

From `langgraph-agents/`, either launch the file directly:

```powershell
uv run python tweet_generator/tweet_generator.py
```

or run it as a package module:

```powershell
uv run python -m tweet_generator.tweet_generator
```

The built-in example requests a tweet about local AI and prints the final reflected response.

## Reflection workflow

Each generator call follows a compact, bounded LangGraph reflection loop:

1. `generate_draft` produces one draft from the bounded conversation history and current request.
2. `reflect` critiques only the current request and latest draft.
3. `revise` replaces the draft using only the latest critique.
4. The reflect/revise pair repeats for the configured number of rounds.

```text
START -> generate_draft -> conditional -> END
                            |
                            `-> reflect -> revise -> conditional -> END
                                             ^             |
                                             `-------------`
```

The workflow makes exactly `1 + (2 * reflection_rounds)` model calls. The default of one reflection round therefore makes three calls instead of the previous eleven-call workflow. Draft and critique fields are replaced on each pass, so intermediate prompts do not grow with the number of rounds.

Only complete successful request/response pairs are committed to bounded session history. A failed generation, reflection, or revision leaves history unchanged. Runtime components are shared for up to eight matching model, URL, and temperature configurations; session history remains isolated per generator. Shared invocation is serialized for compatibility with runtime versions that do not guarantee concurrent model-client safety.

## Use from Python

```python
from tweet_generator.tweet_generator import TweetGenerator, TweetGeneratorSettings

settings = TweetGeneratorSettings(
    reflection_rounds=1,
    max_history_turns=4,
    temperature=0.7,
)
generator = TweetGenerator(settings=settings)

first_tweet = generator("Write a tweet about local AI")
revised_tweet = generator("Make it shorter and more direct")

print(first_tweet)
print(revised_tweet)
```

A generator instance retains up to `max_history_turns` successful request/final-response pairs. Reusing the same instance lets feedback refer to previous results. Use `0` to disable retained history or create a new instance to begin a separate session. Reflection rounds must be a non-negative integer; history size must be a non-negative integer; temperature must be finite and non-negative.

You can also supply configuration explicitly:

```python
from ollama_ai_config import OllamaAIConfig
from tweet_generator.tweet_generator import TweetGenerator

config = OllamaAIConfig()
generator = TweetGenerator(config)
```

## Project structure

```text
langgraph-agents/
|-- ollama_ai_config.py              # compatibility re-export
|-- pyproject.toml
|-- uv.lock
`-- tweet_generator/
    |-- __init__.py
    |-- ollama_ai_config.py          # canonical configuration
    `-- tweet_generator.py
```

- `tweet_generator/ollama_ai_config.py` loads and validates the model name and Ollama server URL.
- The root `ollama_ai_config.py` preserves existing imports without duplicating the implementation.
- `tweet_generator/tweet_generator.py` builds cached generation/reflection/revision runtimes, compiles the compact `StateGraph`, maintains bounded transactional session history, and provides callable and script interfaces.

## Validation

Run Pyright against all project-owned Python files:

```powershell
uv run pyright ollama_ai_config.py tweet_generator/ollama_ai_config.py tweet_generator/tweet_generator.py tweet_generator/__init__.py
```

Run deterministic standard-library tests without contacting Ollama:

```powershell
uv run python -m unittest discover -s tests -v
```

Validate imports without making an Ollama request:

```powershell
uv run python -c "from tweet_generator.tweet_generator import TweetGenerator; assert TweetGenerator is not None"
```

If an editor reports that `langchain_ollama` cannot be resolved, select `langgraph-agents/.venv/Scripts/python.exe` as the workspace's Python interpreter.
