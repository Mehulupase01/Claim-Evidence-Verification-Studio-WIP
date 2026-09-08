# Release Checklist

## Verified in this build

- [x] Requirements and design decisions are recorded.
- [x] The deterministic suite passes: 42 tests, with only two credential-gated tests skipped.
- [x] Text and text-bearing PDF extraction preserve evidence metadata.
- [x] All three verdict paths and evidence-ID grounding are tested.
- [x] Failed verifications are not persisted.
- [x] Repository and Git history secret scan passes.
- [x] Dependency audit reports no known vulnerabilities.
- [x] Compose configuration resolves to one health-checked service.
- [x] The temporary public workspace and `/health` route return HTTP 200 through Cloudflare.
- [x] README, design note, API guide, evaluation record, deployment guide, and handoff agree with the source.

## Owner-dependent release gates

- [ ] Add real R2 and Gemini values to the local `.env`; do not send them through chat or commit them.
- [ ] Run `R2_INTEGRATION=1` and confirm the exact byte round trip.
- [ ] Run `GEMINI_INTEGRATION=1` and confirm a structured supported verdict.
- [ ] Run a real upload -> review -> saved GET through the public URL.
- [ ] Confirm supported, contradicted, and insufficient examples manually.
- [ ] Confirm a bad key and bad R2 configuration return safe errors with clean logs.
- [ ] Verify the no-cache image build and image audit in the fresh CI run.
- [ ] Check the public page from a second browser/device and at a narrow viewport.
- [ ] Stop the Quick Tunnel and any free-tier resources when the review window ends.

Do not describe the submission as fully externally verified until every owner-dependent item is checked.
