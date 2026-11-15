"""The old auth_alpha import path keeps working, warns once, and hands out the same objects."""

import subprocess
import sys

PROBE = """
import warnings
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    from aws_lambda_powertools.utilities.auth_alpha import AuthFailureReason as OldReason
    from aws_lambda_powertools.utilities.auth_alpha import JWTVerifier as OldVerifier
    from aws_lambda_powertools.utilities.auth_alpha.jwt.exceptions import InvalidSignatureError as OldError
    from aws_lambda_powertools.utilities.auth_alpha.oauth2 import OAuth2Client as OldClient
from aws_lambda_powertools.utilities.auth import AuthFailureReason, JWTVerifier, OAuth2Client
from aws_lambda_powertools.utilities.auth.jwt.exceptions import InvalidSignatureError

assert OldVerifier is JWTVerifier
assert OldClient is OAuth2Client
assert OldReason is AuthFailureReason
assert OldError is InvalidSignatureError
categories = [w.category.__name__ for w in caught]
assert categories == ["PowertoolsDeprecationWarning"], categories
assert "aws_lambda_powertools.utilities.auth instead" in str(caught[0].message)
print("ok")
"""


def test_auth_alpha_alias_warns_once_and_shares_objects():
    # GIVEN code written against the alpha namespace
    # WHEN it imports the package and its submodules in a fresh interpreter
    result = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, check=False)

    # THEN one deprecation warning fires and every name is the same object as in the new namespace
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
