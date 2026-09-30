from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.engine import TroubleshootingEngine
from app.models import TroubleshootRequest
from app.validators import WEB_URL


ROOT = Path(__file__).resolve().parents[1]


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = TroubleshootingEngine(ROOT / "data")

    def test_known_query_returns_grounded_plan(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="My camera photos are blurry"))
        self.assertTrue(result.response.contexts)
        self.assertEqual(result.response.contexts[0].title, "Camera Image Blur")

    def test_prevalidated_paraphrase_hits_cache(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="My battery dies too fast"))
        self.assertTrue(result.meta.cache_hit)
        self.assertLess(result.meta.latency_ms, 300)

    def test_unknown_query_fails_closed(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="The moon icon changed color"))
        self.assertEqual(result.response.contexts, [])
        self.assertEqual(result.meta.fallback, "no_match")

    def test_output_contains_no_web_urls(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="Wi-Fi keeps dropping"))
        self.assertIsNone(WEB_URL.search(result.model_dump_json()))

    def test_every_deeplink_exists_in_catalog(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="An app keeps crashing"))
        uris = {
            group.actionableDeeplink.deeplink
            for goal in result.response.contexts
            for action in goal.actions
            for group in action.stepGroups
            if group.actionableDeeplink
        }
        self.assertTrue(uris.issubset(self.engine.allowed_uris))

    def test_critical_actions_are_last(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="The display flashes while scrolling"))
        categories = [a.category.value for a in result.response.contexts[0].actions]
        self.assertEqual(categories[-1], "critical")

    def test_query_variations_follow_contract(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="Touch gestures are unreliable"))
        self.assertGreaterEqual(len(result.query_variations), 8)
        self.assertLessEqual(len(result.query_variations), 10)

    def test_response_round_trips_as_json(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="App notifications are not appearing"))
        parsed = json.loads(result.model_dump_json())
        self.assertEqual(parsed["query"], "App notifications are not appearing")

    def test_multi_issue_complaint_can_return_multiple_contexts(self):
        result = self.engine.troubleshoot(TroubleshootRequest(query="Screen flickers and the battery dies fast"))
        titles = {goal.title for goal in result.response.contexts}
        self.assertIn("Screen Flicker", titles)
        self.assertIn("Battery Fast Drain", titles)


if __name__ == "__main__":
    unittest.main()
