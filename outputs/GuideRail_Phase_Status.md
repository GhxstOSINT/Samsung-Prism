# GuideRail build status by phase

## Phase 1 — Requirement mapping and safety contract

**Status: Complete**

- Converted the Track 2 requirements into an implementation and validation checklist.
- Defined the multi-issue response schema, step ordering, exact Settings-deeplink membership, fallback behavior, and one-interaction-per-step rules.
- Kept synthetic benchmark claims clearly separated from official evaluation claims.

## Phase 2 — Data, retrieval, and cache foundation

**Status: Complete for the supplied prototype data**

- Added normalized knowledge, SIIS-diagnostic, query-variation, and deeplink-catalog loaders.
- Added an official-data preparation utility so organizer assets can replace the synthetic corpus without code changes.
- Implemented multi-query retrieval and a bounded semantic cache with validation-before-admission.

## Phase 3 — Two-stage model engine

**Status: Complete and tested**

- Stage 1 structures the complaint into issue hypotheses and query variations.
- Retrieval supplies evidence and an allowed deeplink subset.
- Stage 2 produces an evidence-constrained troubleshooting plan.
- A strict validator rejects invented URLs, invalid syntax, unsafe ordering, and unsupported output.
- If a configured model is unavailable or fails validation, the engine returns a grounded deterministic fallback.

## Phase 4 — Runnable product

**Status: Complete**

- Responsive web interface and REST API.
- Health and metrics endpoints, request-size limits, security headers, Docker setup, and environment configuration.
- 13 automated tests covering the model path, hallucination rejection, transport, official-data normalization, schema, API, and fallback behavior.
- Synthetic benchmark: 33 cases with 100% top-1, schema, and catalog-deeplink validity on the included demo corpus. These are development results, not official challenge scores.

## Phase 5 — Submission materials

**Status: Complete drafts, ready for team details**

- Submission presentation, research report, AI disclosure, demo script, checklist, benchmark output, and source package are included.
- Repository and release tag are complete. Replace the college/team placeholders and add the final video URL before submission.

## Phase 6 — Organizer integration and official evaluation

**Status: Awaiting external inputs**

The software path is ready, but a final official competition model cannot be claimed until the following are supplied:

1. Official Track 2 starter dataset and exact deeplink catalog.
2. An approved OpenAI-compatible model endpoint, model name, and API credential.
3. Team and institution details.
4. Final demo video.

Until the model endpoint is configured, the live prototype intentionally uses the grounded deterministic fallback. This is a safe operational mode, not a simulated LLM response.
