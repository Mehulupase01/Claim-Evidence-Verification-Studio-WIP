# Verification Ledger

This ledger distinguishes deterministic automated checks from credential-dependent external checks.

| ID | Check | Status | Evidence |
| --- | --- | --- | --- |
| S1 | `.env` absent from the Git index | Pass | `git check-ignore -v .env`; no tracked `.env`. |
| S2 | `.env.example` contains placeholders only | Pass | Manual and pattern scan; every credential field uses `replace_me` or an angle-bracket placeholder. |
| S3 | No credentials in tracked history | Pass | Git history pattern scan returned only license prose, with no credential value. |
| S4 | No credentials in Docker image metadata/layers | Pending | - |
| R1 | Fresh-clone documented start | Pending | - |
| R2 | No-cache image build | Pending | - |
| H1 | Local application boot and health | Pass | Uvicorn started on port 8010; `/health` returned HTTP 200 and the typed JSON body. |
| I1 | Real R2 round trip | Blocked pending user-owned R2 credentials | Never simulated as real. |
| I2 | Real Gemini structured-output smoke test | Blocked pending user-owned Gemini API key | Never simulated as real. |
| I3 | Persisted review round trip | Pending | - |
| A1-A4 | Three semantics and evidence grounding | Pending | - |
| F1-F2 | Unsupported and oversized uploads | Pass | Offline API tests return 415 and 413 before storage. |
| F3 | No extractable text | Pass | Extraction and API tests return a clear 422 with the OCR limitation. |
| T1 | Text/PDF extraction and BM25 retrieval | Pass | Real generated two-page PDF preserves page numbers; known evidence ranks first. |
| F4-F6 | Storage, timeout, and malformed-model failures | Pending | - |
| L1-L2 | Public health and happy path | Blocked pending runtime credentials and a live tunnel/host | - |
| D1-D2 | README exactness and design note completeness | Pending | - |
