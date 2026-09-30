# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Inferred for this build: FastAPI with a dependency-light HTML CSS and JavaScript demo. The REST API is the judged product surface. The web interface demonstrates the same API without requiring a separate frontend toolchain.

## Users

- Primary: Samsung hackathon judges who need to verify functionality and technical depth quickly.
- Production target: customer-support systems handling vague Galaxy device complaints at high volume.
- End beneficiary: device owners who need safe, ordered fixes and direct access to the relevant Settings screen.

## Product Purpose

The product converts a vague device complaint into a validated troubleshooting plan with ordered actions and catalog-grounded Settings deeplinks. Success means the response conforms to the supplied schema, contains no external URLs or invented catalog identifiers, keeps disruptive actions last, and serves validated repeats in under 300 ms.

## Positioning

The product treats the language model as a proposal generator inside a deterministic safety envelope. Retrieval, deeplink resolution, action ordering, schema validation, cache admission, and fallback behavior remain inspectable and enforceable.

## Operating Context

The submission is for Samsung PRISM Generative AI Hackathon 3rd Edition, Theme 2 Smart Guided Troubleshooting Engine. Judges expect a working prototype, reproducible repository, five minute demo, presentation, architecture, results, limitations, Docker support, and a tagged final release.

## Capabilities and Constraints

- POST /v1/troubleshoot returns structured JSON with query variations, contexts, actions, step groups, categories, scores, operational metadata, and catalog deeplinks.
- GET /health reports service readiness.
- Query enrichment produces a canonical technical query and paraphrase family.
- The two-stage engine separates issue and action extraction from deeplink mapping and plan ordering.
- Only supplied reference text may support troubleshooting steps.
- Only exact deeplink values from the catalog may leave the service.
- Web URLs and markdown wrappers are forbidden in output.
- Auto actions precede manual actions. Critical actions remain last.
- Semantic cache hits target P95 latency at or below 300 ms. Cold path targets P95 at or below 8 seconds.
- Starter assets were not attached, so this build includes clearly labeled synthetic sample data and an adapter for the official files.
- Team name, college, member details, GitHub link, and demo link remain open decisions.

## Brand Commitments

Use the working name GuideRail. Keep the tone technical, calm, and evidence-led. Do not reproduce proprietary Samsung product UI or imply Samsung endorsement.

## Evidence on Hand

- Official hackathon overview and Track 2 guide supplied by the user.
- Official submission presentation template and AI disclosure form supplied by the user.
- Other theme guides supplied for cross-checking event expectations, not as Track 2 requirements.
- Research sources from ACL, EMNLP, SIGIR, NeurIPS, and ICLR support the retrieval, constrained generation, grounding, and semantic caching design.
- No official Track 2 starter JSON files or schema.py were supplied. Synthetic fixtures must remain labeled as such.

## Product Principles

- Ground every output in supplied assets.
- Make unsafe or invalid output unrepresentable at the boundary.
- Prefer an inspectable fallback to an impressive hallucination.
- Measure correctness, latency, cost, and cache behavior separately.
- Keep the API contract reusable across at least ten thousand scenarios.

## Accessibility and Inclusion

The demo supports keyboard use, visible focus, high contrast, reduced motion, responsive layout, plain-language recovery messages, and readable JSON output.
