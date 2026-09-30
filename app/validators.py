from __future__ import annotations

import re

from app.models import Goal


WEB_URL = re.compile(r"(?:https?://|www\.|\[[^\]]+\]\([^)]+\))", re.IGNORECASE)
CATEGORY_ORDER = {"auto": 0, "manual": 1, "critical": 2}
INTERACTION_VERBS = {
    "open", "tap", "select", "choose", "turn", "set", "return", "restart", "wipe",
    "remove", "connect", "disconnect", "scan", "pair", "charge", "close", "move",
    "stop", "update", "navigate", "review", "clean", "enable", "disable", "reset",
}


class PlanValidationError(ValueError):
    pass


def validate_plan(goal: Goal, allowed_deeplinks: set[str], reference_text: str) -> None:
    serialized = goal.model_dump_json()
    if WEB_URL.search(serialized):
        raise PlanValidationError("external URL detected")

    categories = [CATEGORY_ORDER[action.category.value] for action in goal.actions]
    if categories != sorted(categories):
        raise PlanValidationError("action hierarchy violation")
    if not 2 <= len(goal.title.split()) <= 3:
        raise PlanValidationError("goal title must contain 2 to 3 words")
    if not goal.goal.startswith("Follow these steps to perform this ") or not goal.goal.endswith(" Troubleshooting"):
        raise PlanValidationError("goal syntax violation")

    evidence = reference_text.lower()
    for action in goal.actions:
        if action.actionName != action.actionName.title():
            raise PlanValidationError("actionName must use title case")
        for group in action.stepGroups:
            if action.category.value == "auto" and not group.actionableDeeplink:
                raise PlanValidationError("auto action requires an actionable deeplink")
            if action.category.value in {"manual", "critical"} and group.actionableDeeplink:
                raise PlanValidationError("manual and critical actions cannot include actionable deeplinks")
            if group.actionableDeeplink:
                uri = group.actionableDeeplink.deeplink
                if uri not in allowed_deeplinks:
                    raise PlanValidationError(f"catalog integrity violation: {uri}")
            for step in group.steps:
                interaction_count = sum(
                    1 for word in re.findall(r"[a-z]+", step.lower()) if word in INTERACTION_VERBS
                )
                if interaction_count > 1 and " and " in step.lower():
                    raise PlanValidationError(f"step contains multiple physical interactions: {step}")
                important = [word for word in re.findall(r"[a-z]{5,}", step.lower()) if word not in {"settings", "select", "choose", "open", "option"}]
                if important and not any(word in evidence for word in important):
                    raise PlanValidationError(f"ungrounded step: {step}")
