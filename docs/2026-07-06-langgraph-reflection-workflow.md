# LangGraph reflection workflow

Date: 2026-07-06

## Changes

- Converted the tweet generator's manual reflection sequence into a compiled `StateGraph` using `MessagesState`.
- Added fixed draft, reflection, and revision nodes and edges.
- Corrected the reflection node's state input, dictionary invocation, class typing, empty-state handling, unsupported-message handling, and partial-state return value.
- Updated `_tweet` to invoke the graph and commit only its final AI response.
- Updated repository guidance and the project README with the graph contract and topology.

## Reasoning

The previous reflection node could not run because it constructed a set instead of an invocation dictionary, annotated message instances where classes were stored, and returned a bare message despite using `StateGraph`. It was also disconnected from tweet generation. Compiling the three-pass workflow makes reflection part of the actual runtime path while preserving final-only conversation history.
