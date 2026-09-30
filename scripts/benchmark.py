from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.engine import TroubleshootingEngine
from app.models import TroubleshootRequest


def percentile(values: list[float], value: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * value)))
    return ordered[index]


def main() -> None:
    engine = TroubleshootingEngine(ROOT / "data")
    scenarios = [(record["id"], query) for record in engine.records for query in record["paraphrases"][:3]]
    latencies, correct, schema_valid, deeplink_valid = [], 0, 0, 0
    for expected_id, query in scenarios:
        start = time.perf_counter()
        response = engine.troubleshoot(TroubleshootRequest(query=query))
        latencies.append((time.perf_counter() - start) * 1000)
        if response.response.contexts:
            schema_valid += 1
            goal = response.response.contexts[0]
            correct += int(goal.evidence_ids[0] == expected_id)
            uris = [
                group.actionableDeeplink.deeplink
                for action in goal.actions for group in action.stepGroups
                if group.actionableDeeplink
            ]
            deeplink_valid += int(all(uri in engine.allowed_uris for uri in uris))
    n = len(scenarios)
    report = {
        "dataset": "synthetic_demo_v1",
        "limitations": "Illustrative benchmark only. Replace with official held-out assets before submission.",
        "scenarios": n,
        "top1_plan_accuracy": round(correct / n, 4),
        "schema_validity": round(schema_valid / n, 4),
        "catalog_deeplink_validity": round(deeplink_valid / n, 4),
        "latency_ms": {
            "p50": round(statistics.median(latencies), 3),
            "p95": round(percentile(latencies, .95), 3),
            "max": round(max(latencies), 3),
        },
        "cache_entries": len(engine.cache),
    }
    output = ROOT / "outputs" / "benchmark_results.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
