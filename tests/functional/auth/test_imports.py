import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("scenario", ["oauth", "static", "remote", "exports", "star"])
def test_auth_imports_in_clean_interpreter(scenario, jwks, claims, issue_token):
    project_root = Path(__file__).parents[3]
    probe = Path(__file__).with_name("_auth_import_probe.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    fixture = {
        "issuer": claims["iss"],
        "audience": claims["aud"],
        "subject": claims["sub"],
        "jwks": jwks,
        "token": issue_token(),
    }

    result = subprocess.run(
        [sys.executable, str(probe), scenario],
        cwd=project_root,
        env=env,
        input=json.dumps(fixture),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
