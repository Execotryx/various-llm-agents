# Direct tweet generator import fix

Date: 2026-07-06

## Changes

- Added the LangGraph project directory to the module search path only when `tweet_generator.py` is executed directly.
- Preserved the existing package-module import behavior.
- Corrected the documented default Ollama model to match the configuration class.

## Reasoning

Direct file execution places the script's own directory, rather than its parent project directory, on Python's module search path. The configuration module is a sibling of the `tweet_generator` package, so the parent directory must be available before importing it. Restricting the adjustment to direct execution avoids changing normal package imports.
