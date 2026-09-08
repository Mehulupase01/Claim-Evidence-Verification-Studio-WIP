# External Verification

This record captures the real-service release pass performed on 8 September 2026. No credential value is stored here, in Git, in the Docker image, or in application logs.

## Runtime

- Docker Compose built `claim-evidence-verifier:local` from the exact Python 3.12.13 base and started it successfully.
- The container reported healthy on port 8000.
- Image configuration and full layer history passed the credential-pattern audit.
- Running container logs contained no configured credential, API-key header, submitted claim, or document text.
- The account-less review tunnel is `https://rounds-cinema-scope-remind.trycloudflare.com` and remains temporary.

## Cloudflare R2

The opt-in integration test used the real `wipstudio` bucket. It wrote a uniquely named byte payload, confirmed the object existed, read the exact bytes back, and deleted the test object. The later public flows persisted their original document, extracted sidecar, and review JSON artifacts in the same bucket.

## Gemini

The supplied project could authenticate and list its available models. Its first generation request produced Google's current new-project retirement response for Gemini 2.5 Flash-Lite. The application default, examples, and tests were moved to the provider-recommended `gemini-3.5-flash-lite`, which is GA and supports structured output. The real schema-constrained smoke test then passed.

## Public API flow

One uploaded copy of `samples/sample_report.txt` produced the following persisted results:

| Expected verdict | POST | Saved GET | Evidence | Review artifact |
| --- | ---: | ---: | ---: | --- |
| `SUPPORTED` | 201 | 200 | 1 passage | `rev_f8fff5fa984e4c158358f72ccf698d00` |
| `CONTRADICTED` | 201 | 200 | 1 passage | `rev_de37f4a744af4e499f3c011ccbeb099b` |
| `INSUFFICIENT_EVIDENCE` | 201 | 200 | 0 passages | `rev_f66124fa064c4b839adfdeedc624653b` |

Every GET body matched its POST body. Evidence text was resolved by the application from the retrieved source chunk rather than accepted as model-authored quotation text.

## Browser flow

Headless Microsoft Edge loaded the public workspace, selected the bundled sample, submitted the supported claim, displayed one grounded passage, and reloaded review `rev_e71bb9ffd04742e7a890d51af37e75a3` from its saved endpoint. The complete result rendered without horizontal overflow at 1440 by 1000 and 390 by 844 pixels.

## Negative checks

Separate calls with deliberately invalid Gemini and R2 credentials reached the real providers and mapped to the application's safe typed errors. Captured logs contained neither the dummy credential marker nor claims, document bytes, provider payloads, or credential-header names. Offline tests continue to cover timeouts, malformed model output, invented evidence IDs, partial-write rollback, unsupported files, oversized uploads, and text-free PDFs.

## WebMCP compatibility

Microsoft Edge did not expose a native WebMCP context, so a preloaded compatibility harness supplied `document.modelContext` before the application script ran. It captured the `verify_text_claim` registration, validated the input schema, untrusted-content annotation, and abort signal, then executed the registered tool itself. The live call returned `SUPPORTED`, one grounded passage, and persisted review `rev_98787a9e210c4897a3ea1d504c78cc32`. This proves the registration and execution contract without claiming native browser support that was not present.

## Required operational cleanup

The credentials used for this pass crossed a non-secret communication channel. The owner must revoke and replace both credentials, update the ignored `.env`, and restart Compose. The Quick Tunnel has no authentication or uptime guarantee and should be stopped when the review window closes.
