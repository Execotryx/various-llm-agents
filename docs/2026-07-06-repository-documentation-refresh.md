# Repository documentation refresh

Date: 2026-07-06

## Changes

- Expanded `AGENTS.md` to cover both Python example areas, their separate dependency workflows, configuration variables, runtime behavior, and validation requirements.
- Documented the tweet generator's two supported launch modes and direct-execution import bootstrap.
- Replaced the empty LangGraph project README with setup, configuration, usage, architecture, troubleshooting, and validation guidance.
- Clarified that the current Ollama example uses LangChain runnable composition even though LangGraph is installed.

## Reasoning

The previous repository guidance covered only part of the Ollama implementation, and the project README was empty. The refreshed documentation is derived from the current source files and manifests so contributors can select the correct environment, configure each example, run the supported entry points, and understand which behavior is implemented today.
