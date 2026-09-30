from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class AssetLoadError(ValueError):
    pass


@dataclass
class AssetBundle:
    records: list[dict]
    deeplinks: list[dict]
    source: str
    version: str
    warnings: list[str] = field(default_factory=list)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetLoadError(f"Could not read {path.name}: {exc}") from exc


def _as_list(payload: Any, keys: tuple[str, ...]) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in keys:
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
        if payload and all(isinstance(value, dict) for value in payload.values()):
            return [{"id": key, **value} for key, value in payload.items()]
    return []


def _first(item: dict, *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", []):
            return value
    return default


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "item"


def normalize_deeplinks(payload: Any) -> list[dict]:
    rows = _as_list(payload, ("deeplinks", "items", "data", "responses"))
    normalized: list[dict] = []
    for index, row in enumerate(rows):
        uri = _first(row, "deeplink", "uri", "url", "actionableDeeplink")
        if isinstance(uri, dict):
            uri = _first(uri, "deeplink", "uri", "url")
        if not isinstance(uri, str) or not uri.startswith("bixby://"):
            continue
        identifier = str(_first(row, "id", "key", "name", default=f"deeplink_{index}"))
        normalized.append({
            "id": _slug(identifier),
            "deeplink": uri,
            "description": str(_first(row, "description", "label", "title", default="Open approved setting")),
            "message": str(_first(row, "message", "instruction", default="Open the approved Settings screen")),
            "classes": _first(row, "classes", "categories", default=None),
            "originalType": _first(row, "originalType", "type", default="settings"),
        })
    if not normalized:
        raise AssetLoadError("No valid bixby:// deeplinks were found")
    seen: set[str] = set()
    for item in normalized:
        if item["deeplink"] in seen:
            raise AssetLoadError(f"Duplicate deeplink URI: {item['deeplink']}")
        seen.add(item["deeplink"])
    return normalized


def normalize_records(payload: Any, siis_payload: Any | None = None) -> list[dict]:
    rows = _as_list(payload, ("queries", "records", "items", "data", "samples"))
    siis_rows = _as_list(siis_payload, ("responses", "items", "data")) if siis_payload is not None else []
    siis_by_id = {str(_first(row, "id", "query_id", "queryId", default="")): row for row in siis_rows}
    normalized: list[dict] = []
    for index, row in enumerate(rows):
        canonical = str(_first(row, "canonical_query", "query", "complaint", "text", default="")).strip()
        reference = str(_first(row, "reference_text", "reference", "answer", "solution", "siis_response", default="")).strip()
        row_id = str(_first(row, "id", "query_id", "queryId", default=f"record_{index}"))
        if not reference and row_id in siis_by_id:
            reference = str(_first(siis_by_id[row_id], "response", "text", "answer", "solution", default="")).strip()
        actions = _first(row, "actions", "steps", default=[])
        if not canonical or not reference or not isinstance(actions, list):
            continue
        normalized_actions: list[dict] = []
        for action_index, action in enumerate(actions):
            if isinstance(action, str):
                action = {"steps": [action]}
            if not isinstance(action, dict):
                continue
            steps = _first(action, "steps", "instructions", default=[])
            if isinstance(steps, str):
                steps = [steps]
            deeplink_id = _first(action, "deeplink_id", "deeplinkId", "catalog_id", "catalogId", default="")
            normalized_actions.append({
                "action_name": str(_first(action, "action_name", "actionName", "title", default=f"Troubleshooting Step {action_index + 1}")),
                "description": str(_first(action, "description", default="It will apply an approved change")),
                "category": str(_first(action, "category", "type", default="manual")).lower(),
                "deeplink_id": _slug(str(deeplink_id)) if deeplink_id else "",
                "steps": [str(step).strip() for step in steps if str(step).strip()],
            })
        if not normalized_actions:
            continue
        title = str(_first(row, "title", "issue", "goal_title", default=canonical))
        paraphrases = _first(row, "paraphrases", "variations", "query_variations", default=[])
        symptoms = _first(row, "symptoms", "keywords", default=[])
        normalized.append({
            "id": _slug(row_id),
            "domain": str(_first(row, "domain", "category", default="General")),
            "title": " ".join(title.split()[:3]).title(),
            "canonical_query": canonical,
            "symptoms": [str(value) for value in symptoms] if isinstance(symptoms, list) else [str(symptoms)],
            "paraphrases": [str(value) for value in paraphrases] if isinstance(paraphrases, list) else [],
            "reference_text": reference,
            "actions": normalized_actions,
        })
    if not normalized:
        raise AssetLoadError("No complete troubleshooting records were found")
    return normalized


def load_assets(fallback_dir: Path) -> AssetBundle:
    official = os.getenv("OFFICIAL_DATA_DIR", "").strip()
    data_dir = Path(official).expanduser().resolve() if official else fallback_dir.resolve()
    if not data_dir.exists():
        raise AssetLoadError(f"Data directory does not exist: {data_dir}")
    deeplink_path = data_dir / "deeplinks.json"
    if not deeplink_path.exists():
        raise AssetLoadError(f"Missing required deeplink catalog: {deeplink_path}")
    deeplinks = normalize_deeplinks(_read_json(deeplink_path))

    normalized_knowledge = data_dir / "knowledge.json"
    if normalized_knowledge.exists():
        records = _as_list(_read_json(normalized_knowledge), ("records", "data"))
        if not records:
            raise AssetLoadError("knowledge.json does not contain records")
    else:
        query_path = data_dir / "queries.json"
        if not query_path.exists():
            raise AssetLoadError("Expected knowledge.json or queries.json")
        siis_path = data_dir / "siis_responses.json"
        records = normalize_records(_read_json(query_path), _read_json(siis_path) if siis_path.exists() else None)

    source = "official" if official else "synthetic_demo"
    version_file = data_dir / "version.txt"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else f"{source}-v1"
    warnings = [] if official else ["Using bundled synthetic demonstration assets"]
    return AssetBundle(records=records, deeplinks=deeplinks, source=source, version=version, warnings=warnings)
