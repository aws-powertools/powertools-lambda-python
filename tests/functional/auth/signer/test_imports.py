"""Importing the signer must not load the JWT dependencies. botocore itself decides about urllib3 and awscrt."""

import subprocess
import sys

PROBE = """
import sys
from aws_lambda_powertools.utilities.auth import SigV4Signer, SignedRequest
loaded = {"jwt", "cryptography"} & set(sys.modules)
assert not loaded, loaded
import os
os.environ.update(AWS_ACCESS_KEY_ID="AKIAEXAMPLE", AWS_SECRET_ACCESS_KEY="x", AWS_REGION="us-east-1")
SigV4Signer(service="execute-api").sign("GET", "https://example.execute-api.us-east-1.amazonaws.com/")
loaded = {"jwt", "cryptography"} & set(sys.modules)
assert not loaded, loaded
print("ok")
"""


def test_signer_imports_only_botocore():
    result = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
