# Changelog

## 1.0.0 - 2026-09-08

- Added bounded TXT and text-PDF ingestion with page-aware chunks.
- Added Cloudflare R2 storage for originals, extraction sidecars, and review artifacts.
- Added deterministic BM25 evidence retrieval.
- Added Gemini structured verification with three verdicts and evidence-ID enforcement.
- Added the reviewer workspace, sample source, saved-review reload, and safe error states.
- Added Docker Compose packaging, a free tunnel path, CI, secret and image audits, dependency auditing, and a measured retrieval corpus.
- Verified real R2 storage, all three Gemini verdicts, persisted public reviews, and browser reload through the live tunnel.
- Migrated the default verifier from Gemini 2.5 Flash-Lite to 3.5 Flash-Lite after the live API closed the older model to new projects.
- Removed a plain-string API-key argument from the verifier so failed test tracebacks cannot expose it.
