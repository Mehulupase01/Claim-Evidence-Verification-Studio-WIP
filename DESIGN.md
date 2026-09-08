# Design Note

## What I built

Claim Evidence Verifier is a deliberately narrow review tool: upload one source, enter one claim, inspect a grounded verdict, and reopen the saved result. It returns `SUPPORTED`, `CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`, but the interface consistently treats that result as assistance rather than a final decision. The reviewer can see the exact passages behind the verdict and retains responsibility for accepting it.

The important safety property is simple: model-written evidence is never trusted. The application labels the retrieved passages with stable IDs, asks Gemini to choose from those IDs, validates the structured response, rejects unknown or repeated references, and fills the final evidence text from the stored source. A fluent answer cannot smuggle an invented quotation into a saved review.

## Why this shape

FastAPI is the only candidate-owned service. It gives the project typed request contracts, generated OpenAPI documentation, and direct control over error behavior without introducing a framework inside a framework. Plain HTML, CSS, and browser JavaScript keep the reviewer workspace fast and readable without a frontend build system. A feature-detected WebMCP action uses the same page flow; browsers without that experimental API simply ignore it.

Cloudflare R2 is the durable boundary because the brief calls for S3-compatible object storage and immutable artifacts fit it well. Each document has an original object and an extracted JSON sidecar; completed reviews are separate JSON objects. The application does not pretend that its local filesystem or process memory is durable. R2 calls use a small boto3 adapter and run off the event loop.

Retrieval is local BM25. For a bounded, single-document workflow, lexical ranking is transparent, quick, and easy to test. A vector database would add another service, embedding cost, index lifecycle, and a new failure mode before the corpus demonstrates a need for semantic retrieval. Chunk IDs and page metadata are stable, so retrieval behavior and citations can be reproduced.

Gemini is called directly with HTTPX. The request includes a JSON Schema and the response is still validated with strict Pydantic models and application-level evidence rules. A direct adapter keeps timeouts, authentication, and the provider payload visible. LangChain, an agent loop, or a general orchestration layer would obscure more than it helps in this three-call path.

Docker Compose contains one health-checked, non-root application container. R2 and Gemini remain managed external services rather than fake local services. The image uses an exact Python patch version and a resolved dependency lock; credentials are injected only when the container starts.

## What I rejected or cut

I did not split upload, extraction, retrieval, and verification into microservices. Their boundaries exist in code and can be separated later, but distributing them now would mostly create deployment and consistency work. I also left out Redis, Postgres, a queue, a JavaScript framework, OCR, authentication, webhooks, and semantic search. None is inherently wrong; none is necessary to prove the core vertical slice.

The main production additions would be identity and tenant isolation, rate limiting, malware scanning and retention controls, relational workflow and audit metadata, asynchronous processing for larger files, and evaluation on representative private data. Retrieval should become hybrid only if that evaluation shows BM25 missing relevant passages.

## AI assistance and one correction

Codex helped reconcile the two source documents, draft the phase plan, implement the vertical slice, generate adversarial tests, and keep the release evidence current. I reviewed the resulting boundaries and used executable checks instead of treating generated code or prose as proof.

One concrete correction happened in the R2 dependency. The first version placed `lru_cache` around a constructor that accepted a Pydantic `Settings` object. Settings instances are not hashable, so dependency resolution would have failed on the first real request. I removed that cache before the route tests and kept the adapter cheap to construct. The change also avoids retaining a credential-bearing settings object as a cache key.

## Open tradeoff

R2 JSON is a good fit for this immutable, low-volume slice, but it is a weak database for querying review state, ownership, or audit relationships. Moving metadata to a relational store adds migrations and another operational dependency; staying object-only makes future search and transactional workflow awkward. The right transition point is when the product needs multi-user review queues or audit reporting, not merely because a database is conventional.
