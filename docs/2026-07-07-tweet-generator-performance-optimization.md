# Tweet generator performance optimization

Date: 2026-07-07

## Changes

- Added validated, immutable `TweetGeneratorSettings` with configurable reflection rounds, bounded history turns, and temperature.
- Replaced accumulating message state with explicit history, request, draft, critique, and counter fields.
- Changed the graph to one draft call followed by configurable reflection/revision pairs, yielding exactly `1 + (2 * rounds)` model calls.
- Removed role reversal and restricted reflection and revision prompts to the latest current-turn values.
- Stored successful history as bounded complete turn pairs and delayed commits until the entire graph succeeds.
- Cached up to eight model-chain and compiled-graph runtimes by model name, base URL, and temperature while keeping session history private to each generator.
- Serialized shared-runtime invocation as a conservative fallback for installed model clients without documented concurrency safety.
- Added deterministic tests for call counts, termination, compact prompts, history bounds, rollback, runtime reuse, session isolation, concurrency, settings, empty input, and both import modes.
- Added deterministic standard-library unit tests and refreshed repository documentation.

## Reasoning

The prior six-generation workflow required eleven sequential Ollama calls and accumulated every intermediate message, increasing both latency and prompt size. Explicit replacement state keeps each refinement pass constant in size, while one default reflection round reduces the normal request to three calls. Bounded transactional history prevents unbounded session growth and partial commits. Runtime caching avoids rebuilding immutable clients, prompts, and graphs without sharing mutable conversation state.

## Validation

- Run Pyright on every changed Python file.
- Run the deterministic `unittest` suite.
- Verify package and direct/debug-style imports without invoking a live Ollama server.
