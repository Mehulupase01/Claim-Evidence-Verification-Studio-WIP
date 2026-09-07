# Handoff

## Current state

The source briefs have been reviewed in full. Phases 0, 1, and 3 are complete. Phase 2's implementation is complete, with its real-cloud gate still waiting for user-owned R2 credentials. Uploads are bounded, extracted in memory, split into page-aware chunks with stable IDs, ranked by a local BM25 service, and saved as an R2 sidecar. The offline suite covers both text and genuine text-bearing PDF fixtures.

## Next gate

Add the Gemini verifier with JSON-schema output, bounded timeout behavior, strict response validation, and rejection of any evidence ID outside the retrieved candidate set.
