from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path

from pydantic import ValidationError

from app.cache import SemanticCache
from app.data_loader import load_assets
from app.llm import (
    ISSUE_SYSTEM_PROMPT,
    PLAN_SYSTEM_PROMPT,
    LLMProviderError,
    OpenAICompatibleProvider,
    issue_user_prompt,
    plan_user_prompt,
)
from app.models import (
    Action,
    ContextDeeplinkResponse,
    Deeplink,
    Goal,
    ResponseMeta,
    StepGroup,
    TraceEvent,
    TroubleshootRequest,
    TroubleshootResponse,
)
from app.retrieval import HybridRetriever, RankedRecord, canonical_query
from app.validators import PlanValidationError, validate_plan


class TroubleshootingEngine:
    def __init__(self, data_dir: Path, provider: OpenAICompatibleProvider | None = None):
        self.data_dir = data_dir
        bundle = load_assets(data_dir)
        self.records = bundle.records
        self.deeplinks = bundle.deeplinks
        self.data_source = bundle.source
        self.asset_warnings = bundle.warnings
        self.catalog = {entry["id"]: entry for entry in self.deeplinks}
        self.allowed_uris = {entry["deeplink"] for entry in self.deeplinks}
        self.catalog_version = bundle.version
        self.records_by_id = {record["id"]: record for record in self.records}
        self.retriever = HybridRetriever(self.records)
        self.cache = SemanticCache(
            threshold=float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.72")),
            max_entries=int(os.getenv("CACHE_MAX_ENTRIES", "100000")),
            ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "86400")),
        )
        self.llm = provider or OpenAICompatibleProvider()
        self.fail_open = os.getenv("LLM_FAIL_OPEN", "1") != "0"
        self._stats_lock = threading.Lock()
        self._stats = {"requests": 0, "fallbacks": 0, "llm_successes": 0, "llm_failures": 0}
        self._validate_assets()
        self._prewarm()

    def _validate_assets(self) -> None:
        if len(self.catalog) != len(self.deeplinks):
            raise ValueError("deeplink IDs must be unique")
        if len(self.records_by_id) != len(self.records):
            raise ValueError("knowledge record IDs must be unique")
        for record in self.records:
            for action in record.get("actions", []):
                deeplink_id = action.get("deeplink_id")
                if action.get("category") == "auto" and deeplink_id not in self.catalog:
                    raise ValueError(f"{record['id']} references unknown deeplink ID: {deeplink_id}")

    def _increment(self, key: str) -> None:
        with self._stats_lock:
            self._stats[key] += 1

    def stats(self) -> dict:
        with self._stats_lock:
            engine = dict(self._stats)
        return {"engine": engine, "cache": self.cache.stats()}

    def _prewarm(self) -> None:
        for record in self.records:
            response = self._build_payload(record, score=1.0)
            for query in [record["canonical_query"], *record.get("paraphrases", [])]:
                self.cache.put(query, response)

    @staticmethod
    def _variations(query: str, record: dict | None, proposed: list[str] | None = None) -> list[str]:
        base = list(proposed or []) + (list(record.get("paraphrases", [])) if record else [])
        templates = [
            query.strip(),
            f"Help with {query.strip().lower()}",
            f"Galaxy issue: {query.strip().lower()}",
            f"How do I fix {query.strip().lower()}?",
            f"Troubleshoot {query.strip().lower()}",
            f"Device problem {query.strip().lower()}",
            f"Settings fix for {query.strip().lower()}",
            f"Why is {query.strip().lower()} happening?",
        ]
        output: list[str] = []
        seen: set[str] = set()
        for value in [*base, *templates]:
            clean = " ".join(str(value).split())
            if clean and clean.lower() not in seen:
                output.append(clean)
                seen.add(clean.lower())
            if len(output) == 10:
                break
        return output[:10]

    def _build_payload(self, record: dict, score: float) -> dict:
        actions = []
        for item in record["actions"]:
            category = item["category"]
            deeplink = self.catalog.get(item.get("deeplink_id", ""))
            actions.append(Action(
                actionName=item["action_name"],
                description=item["description"],
                category=category,
                stepGroups=[StepGroup(
                    steps=item["steps"],
                    actionableDeeplink=Deeplink(
                        deeplink=deeplink["deeplink"],
                        description=deeplink["description"],
                        message=deeplink["message"],
                        classes=deeplink.get("classes"),
                        originalType=deeplink.get("originalType"),
                    ) if category == "auto" and deeplink else None,
                )],
            ))
        goal = Goal(
            goal=f"Follow these steps to perform this {record['title']} Troubleshooting",
            title=record["title"],
            score=round(score, 3),
            actions=actions,
            evidence_ids=[record["id"]],
        )
        validate_plan(goal, self.allowed_uris, record["reference_text"])
        return ContextDeeplinkResponse(contexts=[goal]).model_dump(mode="json")

    @staticmethod
    def _validate_issue_proposal(payload: dict) -> tuple[list[dict], list[str]]:
        issues = payload.get("issues")
        variations = payload.get("variations")
        if not isinstance(issues, list) or not 1 <= len(issues) <= 3:
            raise ValueError("stage-one issues must contain 1 to 3 items")
        clean_issues = []
        for issue in issues:
            if not isinstance(issue, dict):
                raise ValueError("stage-one issue must be an object")
            search_query = " ".join(str(issue.get("search_query", "")).split())
            title = " ".join(str(issue.get("title", "")).split())
            confidence = float(issue.get("confidence", 0))
            if not search_query or not title or not 0 <= confidence <= 1:
                raise ValueError("invalid stage-one issue")
            clean_issues.append({"title": title, "search_query": search_query, "confidence": confidence})
        if not isinstance(variations, list) or not 8 <= len(variations) <= 10:
            raise ValueError("stage-one variations must contain 8 to 10 items")
        clean_variations = [" ".join(str(value).split()) for value in variations if str(value).strip()]
        if len(clean_variations) < 8:
            raise ValueError("too few usable stage-one variations")
        return clean_issues, clean_variations[:10]

    def _retrieve(self, query: str, issues: list[dict], siis_response: str | None) -> list[RankedRecord]:
        searches = [query, *[item["search_query"] for item in issues]]
        if siis_response:
            searches.append(f"{query} {siis_response[:2000]}")
        merged: dict[str, RankedRecord] = {}
        for search in searches:
            for candidate in self.retriever.search(search, top_k=5):
                current = merged.get(candidate.record["id"])
                if current is None or candidate.score > current.score:
                    merged[candidate.record["id"]] = candidate
        return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:5]

    def _catalog_subset(self, records: list[dict]) -> list[dict]:
        ids = {
            action.get("deeplink_id")
            for record in records
            for action in record.get("actions", [])
            if action.get("deeplink_id") in self.catalog
        }
        return [self.catalog[identifier] for identifier in sorted(ids)]

    def _validate_model_plan(self, payload: dict, evidence: list[dict]) -> ContextDeeplinkResponse:
        response = ContextDeeplinkResponse.model_validate(payload)
        evidence_by_id = {item["id"]: item for item in evidence}
        for goal in response.contexts:
            if not goal.evidence_ids or any(identifier not in evidence_by_id for identifier in goal.evidence_ids):
                raise PlanValidationError("model returned unknown or missing evidence IDs")
            reference_text = " ".join(evidence_by_id[identifier]["reference_text"] for identifier in goal.evidence_ids)
            validate_plan(goal, self.allowed_uris, reference_text)
        return response

    def troubleshoot(self, request: TroubleshootRequest) -> TroubleshootResponse:
        self._increment("requests")
        started = time.perf_counter()
        trace: list[TraceEvent] = []
        prompt_tokens = completion_tokens = llm_calls = 0
        cost = 0.0
        proposed_variations: list[str] | None = None
        issues: list[dict] = []

        stage = time.perf_counter()
        normalized = canonical_query(request.query)
        trace.append(TraceEvent(stage="query_enrichment", detail=f"Canonical terms: {normalized}", duration_ms=(time.perf_counter()-stage)*1000))

        stage = time.perf_counter()
        cached, cache_key, cache_score = self.cache.get(request.query)
        trace.append(TraceEvent(stage="semantic_cache", detail=f"Best cache similarity: {cache_score:.2f}", duration_ms=(time.perf_counter()-stage)*1000))
        if cached:
            record_id = cached["contexts"][0]["evidence_ids"][0]
            record = self.records_by_id.get(record_id)
            latency = (time.perf_counter() - started) * 1000
            return TroubleshootResponse(
                query=request.query,
                normalized_query=normalized,
                query_variations=self._variations(request.query, record),
                response=ContextDeeplinkResponse.model_validate(cached),
                meta=ResponseMeta(
                    request_id=str(uuid.uuid4()), latency_ms=round(latency, 2), cache_hit=True,
                    cache_match=cache_key, mode="validated_cache", cost_usd=0.0,
                    catalog_version=self.catalog_version, data_source=self.data_source,
                    model_id=self.llm.model or None, trace=trace,
                ),
            )

        llm_error: str | None = None
        if self.llm.available:
            stage = time.perf_counter()
            try:
                proposal = self.llm.complete_json(ISSUE_SYSTEM_PROMPT, issue_user_prompt(request.query, request.siis_response))
                llm_calls += 1
                prompt_tokens += proposal.prompt_tokens
                completion_tokens += proposal.completion_tokens
                issues, proposed_variations = self._validate_issue_proposal(proposal.data)
                trace.append(TraceEvent(stage="llm_stage_one", detail=f"Structured {len(issues)} issue hypothesis(es)", duration_ms=(time.perf_counter()-stage)*1000))
            except (LLMProviderError, ValueError) as exc:
                llm_error = f"stage_one_{type(exc).__name__}"
                self._increment("llm_failures")
                trace.append(TraceEvent(stage="llm_stage_one", detail=f"Rejected: {llm_error}", duration_ms=(time.perf_counter()-stage)*1000))

        stage = time.perf_counter()
        ranked = self._retrieve(request.query, issues, request.siis_response)
        best = ranked[0] if ranked else None
        detail = "No candidate" if not best else f"{best.record['id']} hybrid={best.score:.2f} lexical={best.lexical_score:.2f} concept={best.semantic_score:.2f}"
        trace.append(TraceEvent(stage="grounded_retrieval", detail=detail, duration_ms=(time.perf_counter()-stage)*1000))
        chosen = [item for item in ranked if item.score >= 0.45][:3]
        record = chosen[0].record if chosen else None
        response = ContextDeeplinkResponse(contexts=[])
        fallback: str | None = None
        mode = "deterministic_grounded_fallback"

        if not chosen:
            fallback = "no_match"
        elif self.llm.available and issues and not llm_error:
            stage = time.perf_counter()
            evidence = [item.record for item in chosen]
            try:
                proposal = self.llm.complete_json(
                    PLAN_SYSTEM_PROMPT,
                    plan_user_prompt(request.query, issues, evidence, self._catalog_subset(evidence)),
                )
                llm_calls += 1
                prompt_tokens += proposal.prompt_tokens
                completion_tokens += proposal.completion_tokens
                response = self._validate_model_plan(proposal.data, evidence)
                if not response.contexts:
                    fallback = "model_insufficient_evidence"
                else:
                    mode = "two_stage_llm_validated"
                    self._increment("llm_successes")
                trace.append(TraceEvent(stage="llm_stage_two", detail=f"{len(response.contexts)} context(s) accepted by deterministic validation", duration_ms=(time.perf_counter()-stage)*1000))
            except (LLMProviderError, ValidationError, PlanValidationError, ValueError) as exc:
                llm_error = f"stage_two_{type(exc).__name__}"
                self._increment("llm_failures")
                trace.append(TraceEvent(stage="llm_stage_two", detail=f"Rejected: {llm_error}", duration_ms=(time.perf_counter()-stage)*1000))
                if not self.fail_open:
                    fallback = "llm_validation_failed"

        if chosen and not response.contexts and (not self.llm.available or self.fail_open) and fallback not in {"model_insufficient_evidence"}:
            stage = time.perf_counter()
            try:
                contexts = []
                for candidate in chosen:
                    contexts.extend(self._build_payload(candidate.record, candidate.score)["contexts"])
                response = ContextDeeplinkResponse.model_validate({"contexts": contexts})
                fallback = llm_error
                trace.append(TraceEvent(stage="deterministic_plan", detail=f"{len(contexts)} grounded context(s) passed all checks", duration_ms=(time.perf_counter()-stage)*1000))
            except (PlanValidationError, ValidationError) as exc:
                fallback = "validation_failed"
                response = ContextDeeplinkResponse(contexts=[])
                trace.append(TraceEvent(stage="validation", detail=str(exc), duration_ms=(time.perf_counter()-stage)*1000))

        if fallback:
            self._increment("fallbacks")
        cost = self.llm.estimated_cost(prompt_tokens, completion_tokens) if hasattr(self.llm, "estimated_cost") else 0.0
        variations = self._variations(request.query, record, proposed_variations)
        latency = (time.perf_counter() - started) * 1000
        result = TroubleshootResponse(
            query=request.query,
            normalized_query=normalized,
            query_variations=variations,
            response=response,
            meta=ResponseMeta(
                request_id=str(uuid.uuid4()), latency_ms=round(latency, 2), cache_hit=False,
                mode=mode, cost_usd=cost, fallback=fallback, catalog_version=self.catalog_version,
                data_source=self.data_source, model_id=self.llm.model or None, llm_calls=llm_calls,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, trace=trace,
            ),
        )
        if response.contexts:
            self.cache.put(request.query, response.model_dump(mode="json"))
            for variation in variations:
                self.cache.put(variation, response.model_dump(mode="json"))
        return result
