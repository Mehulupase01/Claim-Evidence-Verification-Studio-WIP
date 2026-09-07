# Handoff

## Current state

The source briefs have been reviewed in full. Phases 0 and 1 are complete. Phase 2 has a bounded upload route, an explicit R2 adapter, safe failure mapping, an in-memory test double, and a credential-gated real integration test. The local environment has no R2 settings, so the external round-trip gate remains pending and is not represented as passed.

## Next gate

Add text/PDF extraction, stable chunking, deterministic BM25 retrieval, and extracted-sidecar persistence. Keep the real R2 check separately gated until credentials are configured locally.
