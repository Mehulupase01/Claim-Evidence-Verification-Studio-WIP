# Claim Evidence Verifier

Claim Evidence Verifier is a small, grounded review system for checking whether a claim is supported by an uploaded source document. This repository is being implemented phase by phase from the Studio WIP take-home brief and its accompanying master plan.

The target vertical slice is:

```text
upload document -> extract and chunk -> retrieve evidence
                -> structured LLM verdict -> persist review -> human checks result
```

The final README will contain the exact one-command startup path, live/demo guidance, architecture, API reference, verification evidence, limitations, and deployment instructions once every implementation gate has been exercised.

See [DESIGN.md](DESIGN.md) for the reviewer-facing design note and [BUILD_NOTES.md](BUILD_NOTES.md) for the evidence-based implementation log.
