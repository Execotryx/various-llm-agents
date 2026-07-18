# Reflection loop correction

Date: 2026-07-07

## Changes

- Replaced conflicting unconditional graph edges with one bounded conditional reflection loop.
- Added explicit per-invocation iteration and turn-start fields to graph state.
- Scoped reflection role translation to the current invocation instead of retained conversation history.
- Removed the redundant revision node; the generation node now handles drafts and revisions.
- Updated repository guidance and the project README with the actual topology and model-call count.

## Reasoning

The previous continuation check counted state keys rather than iterations and could never terminate. Simultaneous unconditional and conditional edges also kept generation and reflection running after revision branches finished. Explicit iteration state provides deterministic termination, while a current-turn boundary prevents role reversal from corrupting messages retained from earlier calls.
