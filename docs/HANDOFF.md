# Handoff

## Current state

The source briefs have been reviewed in full. Phases 0, 1, and 3 are complete. The production code for Phases 2 and 4 is complete, with both external smoke checks waiting for user-owned credentials. The Gemini adapter sends only retrieved passages, requests JSON-schema output, validates the typed response again locally, and rejects invented or duplicate evidence IDs. No provider response body or API key is logged.

## Next gate

Wire the full review route: load the extracted R2 sidecar, rank candidates, obtain and ground the decision, persist only a valid final review, and support retrieval by review ID.
