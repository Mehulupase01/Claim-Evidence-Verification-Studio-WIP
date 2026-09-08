# Progress

| Phase | State | Evidence |
| --- | --- | --- |
| 0 - Brief and decision log | Complete | Scope, architecture, requirement ledger, placeholder environment, ignore rules, and secret scans passed. |
| 1 - FastAPI foundation | Complete | Four tests pass; Uvicorn booted locally and `/health` returned `200 {"status":"ok"}` with a propagated request ID. |
| 2 - R2 and document upload | Implemented; external gate pending | Bounded upload route and S3-compatible adapter pass offline tests. The real R2 round trip is ready but cannot run without user-owned credentials. |
| 3 - Extraction and retrieval | Complete | Text and real text-PDF fixtures pass extraction tests; stable chunk IDs, page metadata, BM25 ranking, empty-document rejection, and extracted sidecars are verified. |
| 4 - Structured LLM verification | Implemented; external gate pending | Gemini adapter uses JSON Schema, header-based credentials, strict Pydantic validation, a bounded timeout, and evidence-ID grounding. Real smoke test awaits a user-owned API key. |
| 5 - Review persistence | Complete offline; external gate pending | Upload-to-review-to-GET round trips pass for all three verdicts with injected boundaries. Invalid evidence and upstream failures never create review objects. Real R2 plus Gemini E2E awaits credentials. |
| 6 - Reviewer UI | Complete; browser handoff unavailable | Responsive, accessible plain HTML/CSS/JS workspace, sample flow, loading/error states, grounded evidence rendering, saved-review reload, and CSP are covered by route/asset checks. No browser surface was available for the local visual handoff. |
| 7 - Docker reproducibility | Complete | Exact Python image, fully pinned lock, non-root user, healthcheck, and one-service Compose file pass contract tests. A fresh Linux CI runner completed a no-cache build, image audit, Compose start, and health check. |
| 8 - Live deployment path | Public health complete; full E2E pending | Cloudflare Quick Tunnel root and `/health` returned 200 externally. Temporary URL is documented. Public upload/verify/retrieve still requires R2 and Gemini credentials. |
| 9 - Adversarial verification | Complete offline | 42 tests pass, 2 real-provider tests are correctly skipped, secret/history and dependency audits pass, negative logs are clean, and the 5-query retrieval corpus scores 100% top-1 with 0.2181 ms p95. |
| 10 - Clean-room release gate | Complete; owner gates remain | Final README, design note, API guide, release checklist, and changelog are committed. A separate fresh clone passed installation, 42 tests, secret scanning, and Compose resolution; CI passed the complete container path. Real R2/Gemini and manual browser gates still require owner credentials or a supported browser. |
