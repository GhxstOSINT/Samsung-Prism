# GuideRail — 5-minute demonstration script

## Before recording

- Replace every bracketed placeholder in the deck and disclosure.
- Start the service and confirm `/health` returns healthy.
- Keep one browser tab on the GuideRail interface and one terminal ready for an API request.
- Use an official-data example once the starter assets are available. Until then, say “synthetic demonstration corpus” aloud.
- Record one continuous, unedited take under five minutes.

## 0:00–0:35 — Problem and promise

“Device complaints are messy, often contain more than one issue, and can lead a generative model to invent troubleshooting steps or Settings paths. GuideRail turns that complaint into a structured, ordered plan whose actionable deeplinks must come from an approved catalog. If the evidence is weak, the system fails closed instead of guessing.”

Show slide 2, then open the product.

## 0:35–1:15 — Architecture

“The pipeline has five stages: query enrichment, grounded retrieval, plan structuring, exact catalog mapping, and deterministic validation. The model may propose structure, but it is not authoritative. The validator checks the schema, evidence, URLs, catalog membership, step grammar, and action ordering. Only a fully valid result can enter the cache.”

Show slide 4 for no more than 20 seconds, then return to the product.

## 1:15–2:25 — Multi-issue live run

Enter: `My phone gets hot and the battery drains quickly while using the camera.`

“This complaint contains multiple symptoms. GuideRail enriches it, retrieves approved references, and produces more than one goal when the evidence supports separate issue families.”

Point out:

- two or more goals when supported;
- two-to-three-word goal titles;
- ordered auto, manual, and critical actions;
- short descriptions beginning with “It will”;
- one physical interaction per step;
- critical actions placed last.

## 2:25–3:10 — Exact deeplink and JSON proof

Open one verified Settings action.

“Green is reserved for a verified catalog deeplink. The system never generates a web URL or a new Settings identifier. The human view and the API response are the same plan.”

Open the JSON panel and point to `goal`, `score`, `actions`, `steps`, `category`, and `deeplink`.

## 3:10–3:45 — Validated cache

Submit a meaning-equivalent paraphrase of the first complaint.

“The semantic cache is not a shortcut around safety. A plan is admitted only after every validator passes. A repeat or paraphrase can then return on the fast path without another model call.”

Point to the cache status and latency. Report the measured number shown by the running system; do not quote a prepared number.

## 3:45–4:15 — Safe failure

Enter an unsupported complaint such as: `My refrigerator is making a strange noise.`

“This corpus has no supported phone-troubleshooting evidence for that request. GuideRail returns a named low-confidence fallback and no fabricated deeplink.”

## 4:15–4:45 — Evidence and evaluation

“The current engineering baseline passes 13 automated tests, including the two-stage model path, compatible HTTP transport, official-data normalization, and rejection of an invented deeplink. On 33 synthetic paraphrases it achieved 100 percent top-one retrieval, schema validity, and deeplink validity, with a local P95 below one millisecond. These are synthetic smoke-test results, not official Samsung benchmark claims. The final run will report official held-out step accuracy, latency, cache hit rate, and model cost.”

Show slide 8 briefly.

## 4:45–5:00 — Close

“GuideRail is different because it separates generation from authorization: retrieval grounds the plan, the catalog controls navigation, and validation decides what can be returned or cached. The remaining work is official-data integration, held-out evaluation, and submission links.”

End on slide 12.
