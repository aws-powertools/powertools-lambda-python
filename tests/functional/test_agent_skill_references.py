"""The Agent Skill references are generated from the docs; this keeps them from drifting."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_agent_skill_references_are_up_to_date():
    # GIVEN the committed references under .agents/skills
    # WHEN the generator runs in check mode
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_agent_skill_references.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )

    # THEN nothing is stale; the failure output tells the contributor how to regenerate
    assert result.returncode == 0, result.stdout + result.stderr
