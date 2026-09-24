import os
import subprocess
import sys
from pathlib import Path


def test_oauth_client_does_not_import_jwt_or_cryptography():
    root = Path(__file__).parents[4]
    probe = """
import importlib.abc
import sys

class BlockJWT(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"jwt", "cryptography"}:
            raise AssertionError("OAuth imported JWT dependencies")

sys.meta_path.insert(0, BlockJWT())
import aws_lambda_powertools.utilities.auth_alpha as auth
import aws_lambda_powertools.utilities.auth_alpha.oauth2 as oauth
assert "urllib3" not in sys.modules
assert "OAuth2Client" in dir(auth)
assert "OAuth2Client" in dir(oauth)
assert auth.OAuth2Client is oauth.OAuth2Client
client = oauth.OAuth2Client(
    token_url="https://idp.example.com/token",
    client_id="orders",
    client_secret="test-secret",
)
assert repr(client) == "<OAuth2Client>"
try:
    oauth.unknown_attribute
except AttributeError:
    pass
else:
    raise AssertionError("Unexpected module attribute")
assert not {"jwt", "cryptography"} & sys.modules.keys()
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(root), env.get("PYTHONPATH", "")))
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, env=env, check=False)
    assert result.returncode == 0, result.stderr
