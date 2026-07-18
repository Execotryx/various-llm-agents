# Tweet generator reflection workflow

Date: 2026-07-06

## Changes

- Wired the existing reflection prompt and chain into tweet generation.
- Added a draft pass, an internal critique pass, and a final revision pass.
- Kept drafts and critiques out of persistent conversation history.
- Updated repository guidance and the LangGraph project README with the workflow and its latency implications.

## Reasoning

The reflection chain was initialized but never invoked, so generated tweets were returned without review. A fixed three-pass workflow now gives the model explicit critique before finalizing its response. State is committed only after all three calls succeed, preventing partial or failed attempts from contaminating later refinements.
