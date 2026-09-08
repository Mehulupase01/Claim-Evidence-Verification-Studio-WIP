# Evaluation

The test strategy is deliberately small. This product handles one document at a time, so deterministic behavior and failure semantics matter more than a large benchmark that would be hard to explain.

## Automated suite

The credential-free suite currently has 43 passing tests and two credential-gated integration tests. With both real integrations enabled, all 45 tests pass. It covers:

- request and response schema validation;
- bounded upload validation and filename normalization;
- text and real text-bearing PDF extraction;
- stable evidence IDs, page metadata, and BM25 ranking;
- all three verdict classes;
- rejection of invented, duplicated, and missing evidence references;
- persistence and byte-for-byte API round trips;
- missing, corrupt, timeout, malformed-provider, and storage-failure paths;
- cleanup when the extracted sidecar cannot be stored;
- reviewer assets, security headers, and container contracts.

## Retrieval corpus

`evaluation/retrieval_corpus.json` contains four short passages and five known claims. On 8 September 2026, 1,000 retrieval iterations on Python 3.12.13 for Windows produced:

| Measure | Result |
| --- | ---: |
| Top-1 accuracy | 5/5 (100%) |
| Top-3 accuracy | 5/5 (100%) |
| Median retrieval time | 0.1961 ms |
| p95 retrieval time | 0.2181 ms |

These numbers describe only the checked-in synthetic corpus and this machine. They are useful as a regression baseline, not a claim about arbitrary documents or end-to-end network latency. Re-run the measurement with:

```powershell
uv run python scripts/evaluate_retrieval.py --iterations 1000
```

The raw result is stored in `evaluation/results.json`.

## Security and dependency checks

The repository scanner checks tracked and untracked files, plus Git patch history, for private-key markers, common cloud key formats, credential-bearing URLs, and non-placeholder environment assignments. The final Phase 9 run passed. A separate `pip-audit` run initially identified six advisories against pypdf 6.14.2; the parser was upgraded to 6.16.1, after which the audit reported no known vulnerabilities.

## External checks still required

The normal test suite never spends provider quota. The two opt-in tests require the owner's local `.env`:

```powershell
$env:R2_INTEGRATION = '1'
uv run pytest -q tests/integration/test_r2.py

$env:GEMINI_INTEGRATION = '1'
uv run pytest -q tests/integration/test_gemini.py
```

Both tests passed in the release environment on 8 September 2026. They remain opt-in so ordinary local and CI runs are deterministic and never spend provider quota.
