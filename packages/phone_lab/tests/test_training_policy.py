import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.training_policy import assert_training_allowed, read_policy


def test_training_hold_missing_and_invalid_policy_fail_closed(tmp_path):
    missing = tmp_path / "missing.json"
    assert read_policy(missing)["state"] == "held"
    with pytest.raises(Refusal, match="held"):
        assert_training_allowed(missing)
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"schema": "phone-lab-training-policy/1", "state": "held", "reason": "Infrastructure first"}))
    with pytest.raises(Refusal, match="Infrastructure first"):
        assert_training_allowed(policy)
    policy.write_text(json.dumps({"schema": "phone-lab-training-policy/1", "state": "enabled", "reason": "Explicit test authorization"}))
    assert_training_allowed(policy)
    policy.write_text(json.dumps({"schema": "phone-lab-training-policy/1", "state": "enabled", "reason": "Test", "override": True}))
    with pytest.raises(Refusal):
        assert_training_allowed(policy)


def test_actual_training_entrypoint_refuses_before_data_access_or_creating_output(tmp_path):
    package = Path(__file__).resolve().parents[1]
    output = tmp_path / "must-not-exist"
    env = dict(os.environ, PYTHONPATH=str(package / "src"))
    result = subprocess.run([sys.executable, str(package / "tools/vision_pilot.py"),
                             str(tmp_path / "absent-data"), str(output), "--ocr", str(tmp_path / "absent-ocr")],
                            capture_output=True, text=True, env=env)
    assert result.returncode != 0
    assert "Training is held" in result.stderr
    assert "FileNotFoundError" not in result.stderr
    assert not output.exists()
