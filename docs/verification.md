# Verification Ledger

This ledger distinguishes deterministic automated checks from credential-dependent external checks.

| ID | Check | Status | Evidence |
| --- | --- | --- | --- |
| S1 | `.env` absent from the Git index | Pass | `git check-ignore -v .env`; no tracked `.env`. |
| S2 | `.env.example` contains placeholders only | Pass | Manual and pattern scan; every credential field uses `replace_me` or an angle-bracket placeholder. |
| S3 | No credentials in tracked history | Pass | Git history pattern scan returned only license prose, with no credential value. |
| S4 | No credentials in Docker image metadata/layers | Pass | The fresh CI image audit checked Docker configuration, environment, and full layer history. |
| R1 | Fresh-clone documented start | Pass | A clean GitHub checkout built and started the Compose service; an independent Windows clone installed from `uv.lock`, ran tests, and resolved Compose without an `.env`. |
| R2 | No-cache image build | Pass in CI | [GitHub Actions run 34173925390](https://github.com/Mehulupase01/Claim-Evidence-Verification-Studio-WIP/actions/runs/34173925390) built without cache, started through Compose, and passed `/health`. The local Docker Desktop engine remained unavailable. |
| H1 | Local application boot and health | Pass | Uvicorn started on port 8010; `/health` returned HTTP 200 and the typed JSON body. |
| I1 | Real R2 round trip | Blocked pending user-owned R2 credentials | Never simulated as real. |
| I2 | Real Gemini structured-output smoke test | Blocked pending user-owned Gemini API key | Never simulated as real. |
| I3 | Persisted review round trip | Pass offline | POST then GET returns identical typed JSON for all verdict classes using the storage boundary's in-memory test double. |
| A1-A4 | Three semantics and evidence grounding | Pass offline | Mock-transport tests cover all verdicts, unknown IDs, duplicate/empty semantic constraints, and strict JSON. Real Gemini semantics remain I2. |
| F1-F2 | Unsupported and oversized uploads | Pass | Offline API tests return 415 and 413 before storage. |
| F3 | No extractable text | Pass | Extraction and API tests return a clear 422 with the OCR limitation. |
| T1 | Text/PDF extraction and BM25 retrieval | Pass | Real generated two-page PDF preserves page numbers; known evidence ranks first. |
| F4 | Storage failure | Pass offline | Upload route maps the injected failure to a safe 502 with request ID. |
| F5-F6 | Timeout and malformed-model failures | Pass offline | Adapter tests raise bounded typed errors without returning provider payloads. |
| L1 | Public health and workspace | Pass | `https://hose-defendant-correctly-priorities.trycloudflare.com` returned the workspace and `200 {"status":"ok"}` through Cloudflare on 2026-09-08. |
| L2 | Public happy path | Blocked pending runtime credentials | The tunnel is live; R2 and Gemini credentials are absent from this machine. |
| Q1 | Deterministic automated suite | Pass | 42 passed and 2 credential-gated integration tests skipped on 2026-09-08. |
| Q2 | Retrieval regression corpus | Pass | 5/5 top-1 and top-3; median 0.1961 ms, p95 0.2181 ms over 1,000 runs. |
| Q3 | Dependency vulnerability audit | Pass | `pip-audit -r requirements.lock` reported no known vulnerabilities after pypdf was upgraded to 6.16.1. |
| Q4 | Negative-path log review | Pass | Timeout, malformed-output, and storage-failure logs contain operational labels/status only. |
| D1-D2 | README exactness and design note completeness | Pass | Final handoff covers the live URL, single start command, complete environment table, architecture, API, failures, evaluation, AI use, cuts, production priorities, and open tradeoff. |
| U1 | Reviewer workspace assets and security headers | Pass | Root, CSS, JavaScript, sample source, CSP, and untrusted-text rendering assertions pass. |
| U2 | Desktop/mobile visual handoff | Pass | Headless Edge renders at 1440 x 1000 and 390 x 844 show the sample and safe error states without horizontal overflow. The 390 px sample flow also passed through the public tunnel. |
| U3 | WebMCP action contract | Implemented; not run | Registration is feature-detected; no supported browser/WebMCP context was available for execution. |
