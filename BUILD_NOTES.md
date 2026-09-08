# Build Notes

These notes are a record of how the project came together, including the parts that needed correction. They are not intended to be a second README; setup instructions live in [README.md](README.md), and the main architectural reasoning is in [DESIGN.md](DESIGN.md).

## What was delivered

The finished project connects a FastAPI application to Cloudflare R2 and the Gemini API. A reviewer can upload a text document or text-based PDF, check a claim, inspect the supporting or conflicting passages, and reopen the saved review.

The brief's main requirements are covered:

- R2 and Gemini are real external integrations, not local stand-ins.
- Docker Compose is the documented one-command start.
- A temporary public URL is available for the review window.
- `.env.example` contains placeholders, while the real `.env` stays ignored.
- Repository history, image layers, and runtime logs were checked for credentials.
- The README and design note contain the requested handoff information.
- The project uses free-tier services.

## How the build progressed

### Phase 0: scope and architecture

I started by reducing the master plan to one complete review path: upload, extract, retrieve, verify, save, and reopen. I chose one FastAPI application rather than several internal services. R2 and Gemini already provide the two independent service boundaries required by the brief, and additional microservices would have created deployment work without improving the user flow.

The first decision log also set two rules that stayed in place throughout the build: model output would never be accepted as quotation text, and the app had to start even when external credentials were missing so that its health endpoint remained useful.

### Phase 1: application foundation

This phase added the FastAPI shell, typed settings, request IDs, structured logging, error responses, and the initial tests. Configuration is loaded from environment variables and credential fields use Pydantic secret types.

### Phase 2: R2 storage and uploads

I added the S3-compatible R2 adapter and a bounded document upload route. The production code uses boto3, while routine tests use an in-memory implementation of the same small interface. Storage calls run outside the async event loop.

The original file and its extracted sidecar are written under one document ID. If the second write fails, the route removes the first object rather than leaving a half-created document behind.

### Phase 3: extraction and retrieval

Text files and PDFs with embedded text are supported. Extraction keeps page information, normalizes the text, and creates stable passage IDs. A local BM25 implementation ranks those passages for the claim.

Scanned PDFs were left out on purpose. They return a clear error explaining that no text could be extracted, rather than pretending an empty document was processed successfully.

### Phase 4: Gemini verification

The Gemini adapter sends only the claim and the top-ranked passages. The request asks for structured JSON, and the response is checked again with Pydantic before the application uses it.

Evidence IDs receive a second application-level check. Unknown or repeated IDs are rejected, and a verdict that requires evidence cannot be saved without it. The source text shown to the reviewer is always resolved from the retrieved passage set.

### Phase 5: saved reviews

This phase joined storage, retrieval, Gemini, and evidence validation into the complete API flow. Reviews are only written after every validation step succeeds. A saved review can be loaded by ID without relying on process memory.

Tests cover all three verdicts as well as missing documents, storage failures, timeouts, malformed model responses, and invalid evidence references.

### Phase 6: reviewer interface

I built the interface with plain HTML, CSS, and browser JavaScript. It includes sample data, clear loading and error states, evidence cards, and a link for reopening the saved result.

All document and model text is inserted as text rather than HTML. That keeps uploaded content from becoming executable page markup. A feature-detected WebMCP action uses the same visible review flow where the browser supports it and otherwise stays out of the way.

### Phase 7: Docker packaging

The application was packaged as a single non-root container with a health check. Dependencies come from the checked-in lock file, and secrets are supplied only when the container starts. The exact README command, `docker compose up --build`, was tested locally and on a fresh GitHub runner.

### Phase 8: public review link

I used a free Cloudflare Quick Tunnel to expose the local Compose service. This meets the brief's live-URL requirement without changing the application or putting deployment credentials in the repository.

The tradeoff is uptime: the URL works only while the local machine, container, and tunnel are running. It is suitable for a short review period, not permanent hosting.

### Phase 9: hardening and evaluation

I added negative-path tests, a repository and Git-history secret scan, dependency auditing, image checks, and a small retrieval regression set. The five included queries all rank their expected passage first. Over 1,000 runs on this corpus, median retrieval time was 0.1961 ms and p95 was 0.2181 ms.

Those numbers are useful for catching a regression in this project. They should not be read as a broad benchmark for arbitrary documents.

### Phase 10: release verification

The final pass covered a clean Compose build, container health, live R2 and Gemini tests, all three verdicts through the public URL, saved-review reloads, and desktop and mobile browser checks.

The offline suite currently reports 43 passed tests and two intentionally skipped provider tests. Enabling both real integrations produces 45 passed tests. The latest CI release gate also passed.

## Problems I found and fixed

Several useful issues only appeared once the project was exercised outside the simplest test path:

- The first R2 dependency used `lru_cache` with a Pydantic `Settings` object as a key. That object is not hashable, so dependency resolution would have failed on the first request. I removed the cache.
- The first integration-test configuration disabled `.env` loading even though the instructions told the operator to put credentials there. The tests now load the ignored local file but still require an explicit opt-in flag.
- Gemini 2.5 Flash-Lite authenticated successfully but returned a retirement response for the new project. I moved the configuration to Gemini 3.5 Flash-Lite and repeated the real structured-output and public-flow checks.
- An early Gemini failure showed that passing a plain API key as a method argument could expose it in pytest's enhanced traceback. The key is now read from its secret wrapper only where the HTTP header is created, and a regression test checks the traceback.
- `pip-audit` found published advisories for the original pypdf version. I upgraded it to 6.16.1, reran extraction tests, and repeated the audit.
- The first mobile render could grow wider than a 390 px viewport because of intrinsic grid sizing. Explicit minimum constraints fixed the overflow, and both desktop and mobile layouts were rendered again.
- The first secret-scan pattern was too broad and flagged harmless variable names. I narrowed it to actual credential assignment shapes, then reran it across source files and Git history.

These corrections are also the clearest example of how AI was used during the project: it accelerated implementation, but its output was not treated as proof. Real runs, provider responses, audits, and browser checks decided what stayed.

## What I intentionally did not build

The take-home version does not include authentication, OCR, malware scanning, background processing, a webhook, a relational workflow database, or semantic retrieval. It is designed for one bounded source document per review flow.

For a production version, I would start with identity, authorization, tenant-scoped storage, rate limits, file scanning, retention rules, and relational audit metadata. Larger files should be processed asynchronously. I would evaluate hybrid retrieval only after testing against representative documents.

## Final operational note

The code and release checks are complete. Before handing the link to a reviewer, the owner should rotate any credentials that have crossed a non-secret channel, update the ignored local `.env`, restart the container, and confirm that the temporary tunnel is still reachable.
