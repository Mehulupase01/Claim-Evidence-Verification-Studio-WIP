# Design Note

## What I built and why

I built Claim Evidence Verifier to answer a common but time-consuming review question: does a statement in a report actually match the original source?

The workflow is intentionally short. A reviewer uploads a text file or text-based PDF, enters a claim, and receives one of three verdicts: `SUPPORTED`, `CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`. The result includes the passages used as evidence and is saved so somebody else can reopen it later. I chose this problem because it fits the Studio WIP use case in the brief and is useful without needing a large product around it.

The app does not treat Gemini's wording as source material. It gives each retrieved passage a stable ID, asks Gemini to select from those IDs, rejects IDs it never supplied, and copies the displayed quotation from the stored document. That keeps the evidence tied to the upload even if the model produces a confident but incorrect response.

## Choices I made

The application is a single FastAPI service with two external integrations: Cloudflare R2 and the Gemini API. R2 stores the original upload, extracted text, and finished reviews. Gemini handles the final evidence classification. This is enough to demonstrate real service integration without splitting a small request flow into several internal services.

I used plain HTML, CSS, and JavaScript for the interface. A frontend framework would have added another build process without making this three-step workflow easier to use. Docker Compose provides the one-command startup path and runs the app as a non-root user with a health check.

For retrieval, I chose local BM25 rather than embeddings or a vector database. Each review searches one bounded document, so lexical ranking is fast, predictable, and easy to test. If real documents later show that this misses paraphrases or indirect evidence, the retrieval interface can be replaced with a hybrid search without changing the rest of the review flow.

Gemini is called directly with HTTPX instead of through LangChain or an agent framework. The provider call is small, and keeping it visible makes the timeout, JSON Schema, and error handling easier to understand. I considered Postgres for review metadata, but R2 JSON objects were enough for this read-by-ID take-home workflow.

## How I used AI

I used Codex to help compare the brief and master plan, sketch the implementation phases, write code and tests, and review the release checks. I treated those suggestions as drafts: every important path was checked with tests or a real provider call before I kept it.

One generated mistake was an `lru_cache` around the R2 dependency constructor. The cache key included a Pydantic `Settings` object, which is not hashable, so the first real request would have failed while resolving the dependency. I caught it before the route tests, removed the cache, and left the small adapter inexpensive to create. Later testing also caught a possible API-key leak in an enhanced pytest traceback, so the key is now unwrapped only where the request header is built.

## What I left out

I left out authentication, OCR, background jobs, webhooks, semantic search, and a relational database. They are reasonable production features, but none was needed to prove the core review flow. The first production work should be authentication and tenant isolation, rate limiting, malware scanning, retention controls, and a proper audit store. Large-document extraction should then move to a worker rather than holding an HTTP request open.

## The tradeoff I am still unsure about

R2 is a clean fit for immutable documents and reviews, but it becomes awkward once people need queues, ownership, search, or transactional status changes. Adding Postgres now would make the take-home heavier than necessary; waiting too long would make workflow features harder to build. I would make that decision when the first multi-user review queue or audit-reporting requirement appears.
