# Reflection node clarification comments

Date: 2026-07-07

## Changes

- Added comments describing the reflection node's accumulated message state.
- Explained why human and AI roles are reversed for reflection.
- Documented why unsupported message roles are preserved and why critique is returned as human feedback.

## Reasoning

The reflection node intentionally transforms message roles to let the reviewer critique generated output before the revision node runs. The comments make this non-obvious data flow explicit without changing runtime behavior.
