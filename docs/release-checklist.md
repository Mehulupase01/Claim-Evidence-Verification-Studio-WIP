# Release Checklist

## Verified in this build

- [x] Requirements and design decisions are recorded.
- [x] The credential-free suite passes: 43 tests, with only two opt-in integration tests skipped; the real-provider run passes all 45.
- [x] Text and text-bearing PDF extraction preserve evidence metadata.
- [x] All three verdict paths and evidence-ID grounding are tested.
- [x] Failed verifications are not persisted.
- [x] Repository and Git history secret scan passes.
- [x] Dependency audit reports no known vulnerabilities.
- [x] Compose configuration resolves to one health-checked service.
- [x] A fresh CI runner completes the no-cache image build, image audit, Compose start, and health check.
- [x] A separate clean clone installs from the lockfile and passes tests and secret scanning.
- [x] The temporary public workspace and `/health` route return HTTP 200 through Cloudflare.
- [x] Desktop and 390 px Edge renders have no horizontal overflow; the sample and safe-error states are readable.
- [x] Real R2 write/read/delete and Gemini structured-output smoke tests pass.
- [x] Public supported, contradicted, and insufficient reviews persist and reload correctly.
- [x] Real invalid provider credentials produce safe errors and clean logs.
- [x] The WebMCP compatibility harness captures the tool registration and completes a live grounded review.
- [x] README, design note, API guide, evaluation record, deployment guide, and handoff agree with the source.

## Owner-dependent release gates

- [ ] Revoke and replace the R2 and Gemini credentials that crossed a non-secret channel, update `.env`, and restart Compose.
- [ ] Check the public page from a second physical device during the review window.
- [ ] Stop the Quick Tunnel and any free-tier resources when the review window ends.

The application and its two real integrations are externally verified. Do not leave the temporary, unauthenticated deployment unattended, and do not treat the disclosed credentials as safe for continued use.
