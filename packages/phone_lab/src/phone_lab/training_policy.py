from __future__ import annotations

import json
from pathlib import Path

from .benchmark import Refusal

DEFAULT_POLICY = Path(__file__).with_name("training-policy.json")


def read_policy(path=DEFAULT_POLICY):
    path = Path(path)
    if not path.exists():
        return {"schema": "phone-lab-training-policy/1", "state": "held", "reason": "Training policy is unavailable."}
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Refusal("Invalid training policy; training remains held") from error
    if (not isinstance(policy, dict) or set(policy) != {"schema", "state", "reason"}
            or policy["schema"] != "phone-lab-training-policy/1" or policy["state"] not in ("held", "enabled")
            or not isinstance(policy["reason"], str) or not 1 <= len(policy["reason"]) <= 500
            or not policy["reason"].isprintable()):
        raise Refusal("Invalid training policy; training remains held")
    return policy


def assert_training_allowed(path=DEFAULT_POLICY):
    policy = read_policy(path)
    if policy["state"] != "enabled":
        raise Refusal("Training is held: " + policy["reason"])
