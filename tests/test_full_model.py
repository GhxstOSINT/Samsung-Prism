from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.data_loader import load_assets
from app.engine import TroubleshootingEngine
from app.llm import LLMResult
from app.models import TroubleshootRequest


ROOT = Path(__file__).resolve().parents[1]


class FakeTwoStageProvider:
    available = True
    model = "fake-two-stage-model"

    def __init__(self, plan: dict, hallucinate: bool = False):
        self.plan = json.loads(json.dumps(plan))
        self.hallucinate = hallucinate
        self.calls = 0

    def estimated_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.00012

    def complete_json(self, system: str, user: str, timeout=None) -> LLMResult:
        self.calls += 1
        if "stage one" in system:
            return LLMResult(
                data={
                    "issues": [{"title": "Battery Drain", "search_query": "battery drain fast", "confidence": 0.93}],
                    "variations": [f"Battery drain variation {index}" for index in range(1, 9)],
                },
                prompt_tokens=40,
                completion_tokens=24,
            )
        if self.hallucinate:
            self.plan["contexts"][0]["actions"][0]["stepGroups"][0]["actionableDeeplink"]["deeplink"] = "bixby://masked/act/invented"
        return LLMResult(data=self.plan, prompt_tokens=180, completion_tokens=120)


class FullModelTests(unittest.TestCase):
    def _uncached_query(self) -> str:
        return "Charge percentage collapses rapidly during ordinary daytime use"

    def test_two_stage_model_path_is_executed_and_validated(self):
        baseline = TroubleshootingEngine(ROOT / "data")
        plan = baseline._build_payload(baseline.records_by_id["kb_battery_drain"], 0.91)
        provider = FakeTwoStageProvider(plan)
        engine = TroubleshootingEngine(ROOT / "data", provider=provider)

        result = engine.troubleshoot(TroubleshootRequest(query=self._uncached_query()))

        self.assertEqual(provider.calls, 2)
        self.assertEqual(result.meta.llm_calls, 2)
        self.assertEqual(result.meta.mode, "two_stage_llm_validated")
        self.assertEqual(result.meta.model_id, "fake-two-stage-model")
        self.assertEqual(result.response.contexts[0].evidence_ids, ["kb_battery_drain"])
        self.assertGreater(result.meta.prompt_tokens, 0)

    def test_hallucinated_model_deeplink_is_rejected(self):
        baseline = TroubleshootingEngine(ROOT / "data")
        plan = baseline._build_payload(baseline.records_by_id["kb_battery_drain"], 0.91)
        provider = FakeTwoStageProvider(plan, hallucinate=True)
        engine = TroubleshootingEngine(ROOT / "data", provider=provider)

        result = engine.troubleshoot(TroubleshootRequest(query=self._uncached_query()))

        self.assertEqual(provider.calls, 2)
        self.assertEqual(result.meta.mode, "deterministic_grounded_fallback")
        self.assertEqual(result.meta.fallback, "stage_two_PlanValidationError")
        self.assertTrue(result.response.contexts)
        returned = {
            group.actionableDeeplink.deeplink
            for goal in result.response.contexts
            for action in goal.actions
            for group in action.stepGroups
            if group.actionableDeeplink
        }
        self.assertNotIn("bixby://masked/act/invented", returned)

    def test_official_asset_layout_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "deeplinks.json").write_text(json.dumps({
                "deeplinks": [{
                    "key": "battery_usage",
                    "uri": "bixby://official/battery_usage",
                    "label": "Open battery usage",
                }]
            }), encoding="utf-8")
            (folder / "queries.json").write_text(json.dumps({
                "queries": [{
                    "queryId": "Q-1",
                    "query": "Battery drains quickly",
                    "title": "Battery Drain",
                    "actions": [{
                        "actionName": "Battery Usage Settings",
                        "description": "It will identify heavy battery consumers",
                        "category": "auto",
                        "deeplinkId": "battery_usage",
                        "steps": ["Open Battery usage."],
                    }],
                }]
            }), encoding="utf-8")
            (folder / "siis_responses.json").write_text(json.dumps({
                "responses": [{"queryId": "Q-1", "response": "Open Battery usage."}]
            }), encoding="utf-8")
            (folder / "version.txt").write_text("official-test-v1", encoding="utf-8")
            with patch.dict(os.environ, {"OFFICIAL_DATA_DIR": str(folder)}):
                bundle = load_assets(ROOT / "data")

        self.assertEqual(bundle.source, "official")
        self.assertEqual(bundle.version, "official-test-v1")
        self.assertEqual(bundle.records[0]["id"], "q_1")
        self.assertEqual(bundle.deeplinks[0]["deeplink"], "bixby://official/battery_usage")


if __name__ == "__main__":
    unittest.main()
