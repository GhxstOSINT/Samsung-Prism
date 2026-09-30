from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ActionCategory(str, Enum):
    auto = "auto"
    manual = "manual"
    critical = "critical"


class BaseDeeplink(BaseModel):
    deeplink: str

    @field_validator("deeplink")
    @classmethod
    def masked_uri_only(cls, value: str) -> str:
        if not value.startswith("bixby://"):
            raise ValueError("deeplink must use the masked bixby scheme")
        return value


class Deeplink(BaseDeeplink):
    description: str
    message: str = ""
    classes: list[str] | None = None
    originalType: str | None = None


class ValidationDeeplink(BaseDeeplink):
    key: str
    resultType: str | None = None
    condition: str | None = None
    value: str | None = None


class StepGroup(BaseModel):
    steps: list[str] = Field(min_length=1)
    validationDeeplink: ValidationDeeplink | None = None
    actionableDeeplink: Deeplink | None = None


class Action(BaseModel):
    actionName: str
    description: str
    stepGroups: list[StepGroup] = Field(min_length=1)
    category: ActionCategory = ActionCategory.manual

    @field_validator("actionName")
    @classmethod
    def title_case_action(cls, value: str) -> str:
        if len(value.split()) < 2:
            raise ValueError("actionName must identify one screen or feature")
        return value

    @field_validator("description")
    @classmethod
    def exact_description_style(cls, value: str) -> str:
        words = value.split()
        if not value.startswith("It will ") or not 5 <= len(words) <= 7:
            raise ValueError("description must start with 'It will' and contain 5-7 words")
        return value


class Goal(BaseModel):
    goal: str
    title: str
    actions: list[Action] = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class ContextDeeplinkResponse(BaseModel):
    contexts: list[Goal] = Field(default_factory=list)


class TraceEvent(BaseModel):
    stage: str
    detail: str
    duration_ms: float


class ResponseMeta(BaseModel):
    request_id: str
    latency_ms: float
    cache_hit: bool
    cache_match: str | None = None
    mode: str
    cost_usd: float
    fallback: str | None = None
    catalog_version: str
    data_source: str = "unknown"
    model_id: str | None = None
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    prompt_version: str = "guiderail-v1"
    trace: list[TraceEvent]


class TroubleshootResponse(BaseModel):
    query: str
    normalized_query: str
    query_variations: list[str] = Field(min_length=8, max_length=10)
    response: ContextDeeplinkResponse
    meta: ResponseMeta


class TroubleshootRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    siis_response: str | None = Field(default=None, max_length=30000)
    debug: bool = True


class HealthResponse(BaseModel):
    status: str
    catalog_entries: int
    knowledge_records: int
    cache_entries: int
    catalog_version: str
    data_source: str
    llm_available: bool
    model_id: str | None = None
    checks: dict[str, Any]
