# Local Ollama tweet generator

This project generates and iteratively refines tweets with a locally hosted Ollama model. It uses LangChain's `ChatOllama`, prompt templates, and runnable composition. Although LangGraph is installed, the current implementation does not yet build a LangGraph graph.

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

Each generator call performs three sequential Ollama requests:

1. Generate a draft from the request and existing conversation history.
2. Review the draft with a separate reflection prompt and produce actionable criticism.
3. Generate a revised tweet from the draft and criticism.

The draft and critique remain internal. Only the original request and successful final revision are added to conversation history. If any model call fails, that attempt is not committed. This workflow improves the opportunity for revision but has higher latency than a single model call.

## Use from Python

```python
from tweet_generator.tweet_generator import TweetGenerator

generator = TweetGenerator()

first_tweet = generator("Write a tweet about local AI")
revised_tweet = generator("Make it shorter and more direct")

print(first_tweet)
print(revised_tweet)
```

A generator instance retains each successful request and final reflected response. Reusing the same instance lets feedback refer to previous results. Create a new instance to begin with empty conversation history.

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
- `tweet_generator/tweet_generator.py` builds generation and reflection chains, runs draft/critique/revision passes, maintains final conversation history, and provides callable and script interfaces.

## Validation

Run Pyright against all project-owned Python files:

```powershell
uv run pyright ollama_ai_config.py tweet_generator/ollama_ai_config.py tweet_generator/tweet_generator.py tweet_generator/__init__.py
```

Validate imports without making an Ollama request:

```powershell
uv run python -c "from tweet_generator.tweet_generator import TweetGenerator; assert TweetGenerator is not None"
```

If an editor reports that `langchain_ollama` cannot be resolved, select `langgraph-agents/.venv/Scripts/python.exe` as the workspace's Python interpreter.
