from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResult:
    data: dict[str, Any]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class OpenAICompatibleProvider:
    """Two-stage JSON provider for any OpenAI-compatible chat endpoint."""

    def __init__(self) -> None:
        self.base_url = os.getenv("OPENAI_COMPAT_BASE_URL", "").rstrip("/")
        self.model = os.getenv("MODEL_ID", "")
        self.api_key = os.getenv("API_KEY", "")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "12"))
        self.max_retries = max(0, int(os.getenv("LLM_MAX_RETRIES", "1")))
        self.input_price_per_million = float(os.getenv("MODEL_INPUT_USD_PER_MILLION", "0"))
        self.output_price_per_million = float(os.getenv("MODEL_OUTPUT_USD_PER_MILLION", "0"))

    @property
    def available(self) -> bool:
        return bool(self.base_url and self.model)

    def estimated_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return round(
            prompt_tokens * self.input_price_per_million / 1_000_000
            + completion_tokens * self.output_price_per_million / 1_000_000,
            8,
        )

    def complete_json(self, system: str, user: str, timeout: float | None = None) -> LLMResult:
        if not self.available:
            raise LLMProviderError("LLM provider is not configured")
        body = json.dumps({
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, headers=headers)
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                    payload = json.load(response)
                message = payload["choices"][0]["message"]["content"]
                if isinstance(message, list):
                    message = "".join(part.get("text", "") for part in message if isinstance(part, dict))
                data = json.loads(message)
                if not isinstance(data, dict):
                    raise ValueError("model response root must be an object")
                usage = payload.get("usage") or {}
                return LLMResult(
                    data=data,
                    prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
            except (urllib.error.URLError, TimeoutError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.15 * (2 ** attempt))
        raise LLMProviderError(f"LLM request failed after {self.max_retries + 1} attempt(s): {type(last_error).__name__}")


ISSUE_SYSTEM_PROMPT = """You are stage one of a mobile-device troubleshooting engine.
Return JSON only. Extract independent issue hypotheses from the complaint and optional diagnostic text.
Do not propose repair steps or URLs. Use short, retrieval-oriented search queries.
Schema: {"issues":[{"title":"2 to 4 words","search_query":"plain diagnostic query","confidence":0.0}],"variations":["8 to 10 distinct complaint paraphrases"]}.
Confidence must be between 0 and 1. Return at most 3 issues and exactly 8 to 10 variations."""


PLAN_SYSTEM_PROMPT = """You are stage two of a safety-critical mobile troubleshooting engine.
Return JSON only using the supplied response schema. Use only instructions explicitly present in EVIDENCE.
Use only deeplink objects present in CATALOG. Never generate or alter a URI. Never return a web URL.
Each title has 2 to 3 words. Each description has 5 to 7 words and begins exactly with 'It will'.
Each step is one physical interaction. Order actions auto, then manual, then critical; critical must be last.
If evidence is insufficient, return {"contexts":[]}.
Schema: {"contexts":[{"goal":"string","title":"string","score":0.0,"evidence_ids":["id"],"actions":[{"actionName":"Title Case screen or feature","description":"It will ...","category":"auto|manual|critical","stepGroups":[{"steps":["string"],"actionableDeeplink":{"deeplink":"bixby://...","description":"string","message":"string","classes":["string"],"originalType":"string"}}]}]}]}.
For manual or critical actions, omit actionableDeeplink unless the evidence explicitly requires an approved Settings screen."""


def issue_user_prompt(query: str, siis_response: str | None) -> str:
    diagnostic = siis_response.strip() if siis_response else "(none supplied)"
    return f"COMPLAINT:\n{query.strip()}\n\nOPTIONAL_DIAGNOSTIC_TEXT:\n{diagnostic}"


def plan_user_prompt(query: str, issues: list[dict], evidence: list[dict], catalog: list[dict]) -> str:
    safe_evidence = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "domain": item.get("domain"),
            "reference_text": item.get("reference_text"),
            "approved_actions": item.get("actions", []),
        }
        for item in evidence
    ]
    return "\n\n".join([
        f"COMPLAINT:\n{query.strip()}",
        "ISSUE_HYPOTHESES:\n" + json.dumps(issues, ensure_ascii=False),
        "EVIDENCE:\n" + json.dumps(safe_evidence, ensure_ascii=False),
        "CATALOG:\n" + json.dumps(catalog, ensure_ascii=False),
    ])
