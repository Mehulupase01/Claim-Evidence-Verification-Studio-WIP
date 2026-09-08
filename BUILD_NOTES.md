# Build Notes

## Requirements

- [ ] Wire at least two independent external services or APIs that actually communicate with the application.
- [x] Start reproducibly on a fresh machine using one documented command. A fresh GitHub runner built and started the Compose service, and an independent clone passed installation and tests.
- [x] Provide a reviewer-reachable live URL or documented free tunnel path.
- [x] Keep the AI-assisted implementation fully understood and explainable.
- [x] Keep credentials out of the repository, Git history, image layers, and logs. Repository/history scanning and the clean CI image-layer audit pass.
- [x] Use free tiers and document the cost posture.
- [x] Provide exact README run steps, every environment variable, and the live URL status.
- [x] Commit a placeholder-only `.env.example` and ignore `.env`.
- [x] Deliver a concise design note addressing all five requested prompts.
- [x] Demonstrate upload, grounded verdict, evidence display, persistence, and retrieval with offline service boundaries. The real-provider run remains pending.
- [x] Handle unsupported, oversized, unextractable, missing, storage-failure, malformed-model, and timeout paths safely.

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
| 3 | Codex added bounded text/PDF extraction, stable chunking, and BM25 retrieval. | Kept offsets tied to normalized page text and stored the full extracted artifact beside the original. | Reviews can be repeated without reparsing the upload, and evidence always retains its source page. |
| 4 | Codex added the Gemini structured-output adapter and adversarial response tests. | Used the API key in a header, bounded each request, and retained application-side schema and evidence-ID checks. | Provider-side JSON structure helps, but only the application can enforce that selected citations came from its candidate set. |
| 5 | Codex wired document artifacts, retrieval, verification, evidence resolution, and review persistence into one readable route. | Persist only after every schema and grounding check passes; failed attempts remain in request-scoped logs only. | A saved review is always a valid human-review artifact, never a partial upstream response. |
| 6 | Codex built the reviewer workspace and its loading, error, result, and saved-review states. | Used plain browser APIs and text-only DOM updates for source and model content; added one feature-detected WebMCP action over the same visible flow. | There is no frontend build chain, and untrusted evidence never enters the page through HTML injection. |
| 7 | Codex packaged the app as one non-root, health-checked container. | Used an exact Python patch tag and a fully resolved lock export; runtime secrets are supplied only when the container starts. | The image stays small and auditable, while Compose remains the single start command. |
| 8 | Codex opened and verified a free Cloudflare Quick Tunnel to the local app. | Kept deployment outside the application and documented the URL's temporary nature and lack of SLA. | Public reachability is proven without coupling the code to a host or committing deployment credentials. |
| 9 | Codex audited the failure matrix, added CI, a repository/history secret scanner, and a measured retrieval corpus. | Added rollback for split document writes and upgraded the PDF parser after a live advisory scan. | Release evidence now covers consistency and dependency risk, not only route behavior. |
| 10 | Codex wrote the reviewer handoff, moved the clean image build into CI, and rendered the live UI at desktop and mobile widths. | Kept verified facts separate from owner-dependent R2/Gemini and unavailable WebMCP gates. | The submission is useful now without overstating what this credential-free environment proved. |

## Bugs and Corrections

During Phase 2, Codex first wrapped the R2 constructor in `lru_cache` with a `Settings` object as the cache key. Pydantic settings objects are not hashable, so that would have failed on the first real dependency resolution. The cache was removed before the route tests; creating the small adapter per request keeps the code correct and avoids retaining credential-bearing settings in a cache key.

During Phase 7, Docker Desktop was installed but its Linux engine and Windows service were stopped. The service could not be started from this non-elevated session, and no Podman or alternate container builder was installed. That local limitation remains, but the Phase 10 GitHub runner completed the no-cache Compose build, image audit, container start, and health check successfully.

During Phase 9, `pip-audit` found six published advisories against pypdf 6.14.2. The dependency was upgraded to 6.16.1 and the full extraction suite was rerun before the audit was allowed to pass. The first secret-scanner expression also matched ordinary variable names such as `TOKEN_PATTERN`; it was narrowed to uppercase credential assignment names, then rerun across source and history.

During the Phase 10 pixel check, the first 390 px render showed that intrinsic grid sizing could push the workflow and review card beyond the viewport. Explicit zero-minimum grid tracks and child constraints removed the overflow. Fresh desktop and mobile Edge renders then loaded the sample, showed the expected safe missing-storage error, and reported no horizontal overflow; the same mobile check passed through the public tunnel.

## Cuts

OCR, authentication, asynchronous processing, relational metadata, advanced retrieval, and the optional webhook are deliberately excluded until every core release gate is green.

## Production Hardening

Prioritized after the take-home boundary: authentication and authorization, malware scanning plus retention controls, relational workflow/audit metadata, rate limiting, asynchronous extraction for large files, distributed tracing, and a broader evaluation corpus.

## Open Tradeoff

R2 JSON artifacts minimize infrastructure and fit immutable review objects, but they do not support efficient querying or transactional workflow state. The point at which review search, ownership, or audit relationships justify a relational database remains the principal open tradeoff.
