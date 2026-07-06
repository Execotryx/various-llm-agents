# Ollama AI configuration scaffold

Date: 2026-07-06

## Changes

- Added `OllamaAIConfig` for configuring a local Ollama model and server URL.
- Added repository-level `.env` loading so local settings remain outside source control.
- Added `python-dotenv` as a runtime dependency and Pyright as a development dependency.
- Documented the Ollama environment variables and validation workflow in `AGENTS.md`.

## Reasoning

The LangGraph examples need one reusable source of Ollama connection settings. Environment variables keep model and endpoint choices configurable across machines, while usable local defaults avoid mandatory setup for the standard Ollama endpoint.
