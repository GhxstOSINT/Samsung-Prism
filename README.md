# GuideRail Smart Guided Troubleshooting Engine

GuideRail is a complete, configurable Track 2 application foundation for the Samsung PRISM Y2026 GenAI Hackathon. It converts vague or multi-issue device complaints into ordered troubleshooting JSON and maps eligible actions to exact allow-listed Settings deeplinks.

Repository: https://github.com/GhxstOSINT/Samsung-Prism

The application supports two runtime modes:

1. **Two-stage model mode** — a configured OpenAI-compatible model first structures issues and query variations, then proposes a plan using only retrieved evidence and candidate catalog entries.
2. **Deterministic grounded fallback** — the application remains runnable when a model is unavailable or its proposal fails validation.

In both modes, retrieval, evidence IDs, the deeplink catalog, schema validation, atomic-step rules, action ordering, and cache admission remain authoritative.

## Implemented capabilities

- `POST /v1/troubleshoot` with strict Pydantic request and response models
- `GET /health` for asset and model readiness
- `GET /metrics` for engine and cache counters
- Optional SIIS diagnostic text in both the API and browser interface
- Stage-one issue extraction and 8–10 query variations
- Stage-two evidence-constrained JSON plan proposal
- Hybrid BM25/concept retrieval with multi-issue candidate fusion
- Exact deeplink allow-list; generated or modified URIs are rejected
- Auto, manual, and critical action ordering
- One-interaction-per-step validation
- External URL, missing evidence, unknown evidence ID, and ungrounded-step rejection
- Indexed validated semantic cache suitable for large paraphrase sets
- Automatic fallback when the model times out, returns malformed JSON, or violates safety rules
- Token and estimated-cost reporting
- Official-data normalization pipeline
- Responsive judge-facing interface, Docker image, tests, and benchmark harness

## Phase status

- Phase 1 — contract, schema, catalog, and validators: complete
- Phase 2 — scalable retrieval, cache, SIIS handling, and official-data adapter: complete
- Phase 3 — real two-call model orchestration and deterministic rejection/fallback: complete
- Phase 4 — API hardening, metrics, tests, Docker, and UI integration: complete
- Phase 5 — ingest official starter data and run the official held-out evaluation: waiting for organizer assets
- Phase 6 — configure the selected production model and publish submission links: waiting for team credentials and links

## Run immediately

Python 3.10–3.12 is supported.

```bash
python -m pip install -r requirements.txt
python -m app.server
```

Open `http://127.0.0.1:8000`.

Without model configuration, the product uses the deterministic grounded fallback and clearly reports that mode.

## Configure the full two-stage model path

Copy `.env.example` to `.env` or export the equivalent variables:

```text
OPENAI_COMPAT_BASE_URL=http://localhost:11434/v1
MODEL_ID=your-json-capable-model
API_KEY=optional-key
LLM_TIMEOUT_SECONDS=12
LLM_MAX_RETRIES=1
LLM_FAIL_OPEN=1
MODEL_INPUT_USD_PER_MILLION=0
MODEL_OUTPUT_USD_PER_MILLION=0
```

`OPENAI_COMPAT_BASE_URL` can point to a permitted hosted endpoint or a local OpenAI-compatible runtime. The application never logs the API key.

The two model calls are:

1. Complaint and SIIS text → up to three issue hypotheses plus 8–10 paraphrases.
2. Complaint, hypotheses, retrieved evidence, and a restricted catalog subset → structured plan proposal.

The second response is served only after Pydantic parsing and deterministic validation. A model-proposed URI must be byte-for-byte present in the loaded catalog.

## Load the official starter assets

Place the organizer files in `official_data/`:

```text
official_data/
  queries.json
  siis_responses.json
  deeplinks.json
  schema.py
```

Normalize and validate them:

```bash
python scripts/prepare_official_data.py official_data data_official --version official-v1
```

Then run with:

```text
OFFICIAL_DATA_DIR=/absolute/path/to/data_official
```

The adapter accepts common list and keyed-object layouts and reports incomplete records, duplicate URIs, and auto actions referencing unknown catalog IDs. The organizer’s exact schema remains authoritative; update the field mapping if its names differ from the documented variants.

## API example

```bash
curl -X POST http://127.0.0.1:8000/v1/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"query":"My battery dies too fast","siis_response":"Battery health check completed"}'
```

The response includes normalized terms, query variations, one or more validated contexts, latency, cache state, model mode, token usage, estimated cost, data provenance, and a per-stage trace.

## Tests and evaluation

```bash
python -m unittest discover -s tests -v
python scripts/benchmark.py
```

The tests cover deterministic behavior, multi-issue routing, strict JSON, exact catalog membership, critical ordering, the two-stage model path, hallucinated-deeplink rejection, real OpenAI-compatible HTTP transport, and official-asset normalization.

The bundled benchmark uses synthetic demonstration data. Do not present its results as official or real-world performance. Once the official assets are loaded, create a separate held-out set and report:

- step accuracy and error categories;
- schema validity;
- exact deeplink validity;
- semantic-cache hit rate;
- warm and cold P50/P95 latency;
- false-accept and safe-fallback rates;
- model tokens and cost per resolved complaint.

## Docker

```bash
docker build -t guiderail .
docker run --rm -p 8000:8000 --env-file .env guiderail
```

Or use `docker compose up --build`. The image runs as a non-root user and includes a health check.

## Current data boundary

The files currently under `data/` are masked synthetic demonstration fixtures: 11 reference plans and 15 deeplinks. They exist to make the full application testable without misrepresenting organizer data. The engine and import pipeline are ready for the official 10k+ scenario corpus, but the official corpus and final held-out results cannot be manufactured from the theme guide.
