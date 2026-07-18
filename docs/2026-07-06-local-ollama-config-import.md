# Local Ollama configuration import

Date: 2026-07-06

## Changes

- Placed the canonical `OllamaAIConfig` implementation beside the tweet generator.
- Replaced the debugger-sensitive `sys.path` mutation with direct-local and package-relative imports.
- Converted the previous root configuration module into a compatibility re-export.
- Updated repository and project documentation with the new ownership and validation paths.

## Reasoning

Executing `tweet_generator.py` directly should resolve its dependencies from its own directory without mutating Python's module search path. Keeping one canonical implementation beside the generator supports direct debugging, while the root re-export prevents existing callers from breaking and avoids maintaining two divergent configuration classes.
