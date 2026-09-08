# Verification Ledger

This ledger distinguishes deterministic automated checks from credential-dependent external checks.

| ID | Check | Status | Evidence |
| --- | --- | --- | --- |
| S1 | `.env` absent from the Git index | Pass | `git check-ignore -v .env`; no tracked `.env`. |
| S2 | `.env.example` contains placeholders only | Pass | Manual and pattern scan; every credential field uses `replace_me` or an angle-bracket placeholder. |
| S3 | No credentials in tracked history | Pass | Git history pattern scan returned only license prose, with no credential value. |
| S4 | No credentials in Docker image metadata/layers | Pass | The fresh CI image audit checked Docker configuration, environment, and full layer history. |
| R1 | Fresh-clone documented start | Pass | A clean GitHub checkout built and started the Compose service; an independent Windows clone installed from `uv.lock`, ran tests, and resolved Compose without an `.env`. |
| R2 | No-cache image build | Pass in CI and local build | [GitHub Actions run 34198792268](https://github.com/Mehulupase01/Claim-Evidence-Verification-Studio-WIP/actions/runs/34198792268) built the verified release without cache, started it through Compose, and passed `/health`; the documented local Compose build passes too. |
| H1 | Local application boot and health | Pass | The Compose container is healthy on port 8000 and returns the typed `200 {"status":"ok"}` response. |
| I1 | Real R2 round trip | Pass | A uniquely named object was written to `wipstudio`, checked, read byte for byte, and deleted. |
| I2 | Real Gemini structured-output smoke test | Pass | Gemini 3.5 Flash-Lite returned a schema-valid supported verdict with the supplied evidence ID. |
| I3 | Persisted review round trip | Pass real and offline | Public POST then GET returned identical typed JSON for all three verdicts against R2. |
| A1-A4 | Three semantics and evidence grounding | Pass real and offline | Public calls returned the expected supported, contradicted, and insufficient verdicts; application-side tests reject unknown, duplicate, or missing required evidence IDs. |
| F1-F2 | Unsupported and oversized uploads | Pass | Offline API tests return 415 and 413 before storage. |
| F3 | No extractable text | Pass | Extraction and API tests return a clear 422 with the OCR limitation. |
| T1 | Text/PDF extraction and BM25 retrieval | Pass | Real generated two-page PDF preserves page numbers; known evidence ranks first. |
| F4 | Storage failure | Pass real and offline | A real invalid R2 credential maps to the safe storage error without credentials or content in logs; injected route tests return 502 with a request ID. |
| F5-F6 | Timeout and malformed-model failures | Pass offline | Adapter tests raise bounded typed errors without returning provider payloads. |
| L1 | Public health and workspace | Pass | `https://rounds-cinema-scope-remind.trycloudflare.com` returns the workspace and typed health response through Cloudflare. |
| L2 | Public happy path | Pass | A real TXT upload produced all three expected verdicts, each persisted and retrieved from R2; the browser UI also completed and reloaded a supported review. |
| Q1 | Automated suite | Pass | 43 passed and 2 intentional external skips without credentials; 45 passed with both real integration flags on 2026-09-08. |
| Q2 | Retrieval regression corpus | Pass | 5/5 top-1 and top-3; median 0.1961 ms, p95 0.2181 ms over 1,000 runs. |
| Q3 | Dependency vulnerability audit | Pass | `pip-audit -r requirements.lock` reported no known vulnerabilities after pypdf was upgraded to 6.16.1. |
| Q4 | Negative-path log review | Pass | Timeout, malformed-output, and storage-failure logs contain operational labels/status only. |
| D1-D2 | README exactness and design note completeness | Pass | Final handoff covers the live URL, single start command, complete environment table, architecture, API, failures, evaluation, AI use, cuts, production priorities, and open tradeoff. |
| U1 | Reviewer workspace assets and security headers | Pass | Root, CSS, JavaScript, sample source, CSP, and untrusted-text rendering assertions pass. |
| U2 | Desktop/mobile visual handoff | Pass | Headless Edge renders the real supported result at 1440 x 1000 and 390 x 844 without horizontal overflow; evidence and saved-review controls remain readable. |
| U3 | WebMCP action contract | Pass in compatibility harness | A preloaded `document.modelContext` captured the registered schema, abort signal, and annotations; executing the real tool produced a persisted supported review with one grounded passage. Native browser support was unavailable. |
