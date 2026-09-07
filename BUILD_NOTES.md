# Build Notes

## Requirements

- [ ] Wire at least two independent external services or APIs that actually communicate with the application.
- [ ] Start reproducibly on a fresh machine using one documented command.
- [ ] Provide a reviewer-reachable live URL or documented free tunnel path.
- [ ] Keep the AI-assisted implementation fully understood and explainable.
- [ ] Keep credentials out of the repository, Git history, image layers, and logs.
- [ ] Use free tiers and document the cost posture.
- [ ] Provide exact README run steps, every environment variable, and the live URL status.
- [ ] Commit a placeholder-only `.env.example` and ignore `.env`.
- [ ] Deliver a concise design note addressing all five requested prompts.
- [ ] Demonstrate upload, grounded verdict, evidence display, persistence, and retrieval.
- [ ] Handle unsupported, oversized, unextractable, missing, storage-failure, malformed-model, and timeout paths safely.

## Scope

### MVP

- One `.txt` or text-based `.pdf` per verification request.
- Cloudflare R2 for original documents, extracted sidecars, and saved reviews.
- Conservative text chunking with stable evidence IDs and page metadata.
- Deterministic BM25 retrieval behind a small interface.
- Gemini structured output restricted to the retrieved passages.
- Exactly three verdicts: `SUPPORTED`, `CONTRADICTED`, and `INSUFFICIENT_EVIDENCE`.
- Server-side evidence resolution; the model never authors displayed quotations.
- FastAPI JSON API plus one plain HTML/CSS/JavaScript reviewer surface.
- Request IDs, structured safe logs, bounded uploads, timeouts, and typed errors.
- Docker Compose as the single primary start command.

### Non-goals

- Agents, LangChain, LangGraph, autonomous tool selection, or multi-agent orchestration.
- Vector databases, embeddings, rerankers, knowledge graphs, or GraphRAG.
- Postgres, Redis, Celery, Kafka, Kubernetes, or background queues.
- OCR, malware scanning, production authentication, multi-tenancy, or a full observability stack.
- React, Vite, Tailwind, or another frontend build system.
- Expensive benchmark infrastructure or a large evaluation corpus.

## Decisions

| Phase | Decision | Reason |
| --- | --- | --- |
| 0 | Keep one FastAPI application as the orchestration boundary. | R2 and Gemini are the two real external services; splitting the candidate code would add fake complexity. |
| 0 | Use Cloudflare R2 Standard storage through its S3-compatible API. | It directly matches the Studio environment and currently includes a small free allowance. |
| 0 | Use Gemini 2.5 Flash-Lite through direct HTTPS. | It currently supports structured output and free-tier token usage; direct HTTP avoids a provider SDK dependency. |
| 0 | Implement BM25 locally. | The per-document corpus is small, lexical retrieval is deterministic, and a short implementation avoids another dependency. |
| 0 | Persist review JSON in R2. | It keeps the take-home small; relational persistence becomes preferable when reviews need querying, ownership, or workflow state. |
| 0 | Do not validate external credentials during application startup. | `/health` and the reviewer shell should boot cleanly; an invoked integration fails clearly if its settings are absent. |

## Dependencies

Phase 0 added no implementation dependency. Phase 1 introduced the following pinned packages:

| Dependency | Why it is here |
| --- | --- |
| FastAPI and Pydantic | Typed HTTP routes and strict request/response contracts. |
| pydantic-settings | One environment-backed settings model with secret-aware values. |
| Uvicorn | The small ASGI server used locally and in the container. |
| python-multipart | Bounded file uploads in Phase 2. |
| boto3 | Cloudflare R2's supported S3-compatible client path in Phase 2. |
| HTTPX | A bounded direct Gemini HTTP call in Phase 4 and in-process API tests. |
| pypdf | Text-based PDF extraction in Phase 3. |
| pytest and pytest-asyncio | Deterministic offline verification. |

## AI Assistance Log

| Phase | Assistance | Accepted or changed | Why |
| --- | --- | --- | --- |
| 0 | Codex reconciled the Studio brief, master plan, and empty repository into a phase plan. | Accepted the prescribed right-sized architecture; current provider availability was checked against official documentation. | Prevents scope drift and avoids selecting a discontinued or paid-only model. |
| 1 | Codex created the typed application shell, settings, request context, and schemas. | Kept the settings lazy so missing external credentials do not take down the health endpoint. | A reviewer can start and diagnose the service before configuring optional request paths. |
| 2 | Codex implemented an R2 adapter and the first document-upload route. | Kept the adapter small, made boto3 calls off the event loop, and put an in-memory test double behind the same contract. | The production path is a real S3-compatible API while routine tests remain fast and offline. |

## Bugs and Corrections

During Phase 2, Codex first wrapped the R2 constructor in `lru_cache` with a `Settings` object as the cache key. Pydantic settings objects are not hashable, so that would have failed on the first real dependency resolution. The cache was removed before the route tests; creating the small adapter per request keeps the code correct and avoids retaining credential-bearing settings in a cache key.

## Cuts

OCR, authentication, asynchronous processing, relational metadata, advanced retrieval, and the optional webhook are deliberately excluded until every core release gate is green.

## Production Hardening

Prioritized after the take-home boundary: authentication and authorization, malware scanning plus retention controls, relational workflow/audit metadata, rate limiting, asynchronous extraction for large files, distributed tracing, and a broader evaluation corpus.

## Open Tradeoff

R2 JSON artifacts minimize infrastructure and fit immutable review objects, but they do not support efficient querying or transactional workflow state. The point at which review search, ownership, or audit relationships justify a relational database remains the principal open tradeoff.
