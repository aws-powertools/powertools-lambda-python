"""Exercise public Auth imports without dependencies preloaded by pytest."""

import importlib
import importlib.abc
import inspect
import json
import sys


class BlockImports(importlib.abc.MetaPathFinder):
    def __init__(self, *names):
        self.names = names

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self.names:
            raise ImportError(f"Unexpected optional dependency: {fullname}")


scenario = sys.argv[1]

if scenario == "oauth":
    sys.meta_path.insert(0, BlockImports("jwt", "cryptography"))

    from aws_lambda_powertools.utilities.auth import OAuth2Client

    client = OAuth2Client(
        token_url="https://idp.example.com/token",
        client_id="test-client",
        client_secret="test-secret",
    )
    assert "jwt" not in sys.modules
    assert "cryptography" not in sys.modules
elif scenario == "static":
    sys.meta_path.insert(0, BlockImports("urllib3"))

    from aws_lambda_powertools.utilities.auth import JWTVerifier
    from aws_lambda_powertools.utilities.auth.exceptions import InvalidSignatureError

    fixture = json.load(sys.stdin)
    verifier = JWTVerifier(
        issuer=fixture["issuer"],
        audience=fixture["audience"],
        algorithms=["RS256"],
        jwks=fixture["jwks"],
    )
    assert verifier.verify(fixture["token"])["sub"] == fixture["subject"]

    signed, signature = fixture["token"].rsplit(".", 1)
    invalid_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    try:
        verifier.verify(f"{signed}.{invalid_signature}")
    except InvalidSignatureError:
        pass
    else:
        raise AssertionError("Invalid signature was accepted")
    assert "urllib3" not in sys.modules
elif scenario == "remote":
    from aws_lambda_powertools.utilities.auth import JWTVerifier

    assert "urllib3" not in sys.modules
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
    )
    assert "urllib3" in sys.modules
elif scenario == "exports":
    auth = importlib.import_module("aws_lambda_powertools.utilities.auth")

    assert {"JWTVerifier", "OAuth2Client"} <= set(dir(auth))
    assert not {"jwt", "cryptography", "urllib3"} & sys.modules.keys()
    try:
        _ = auth.unknown_attribute
    except AttributeError:
        pass
    else:
        raise AssertionError("An unknown attribute did not raise AttributeError")
    assert not {"jwt", "cryptography", "urllib3"} & sys.modules.keys()

    members = dict(inspect.getmembers(auth))
    assert members["JWTVerifier"] is auth.JWTVerifier
    assert members["OAuth2Client"] is auth.OAuth2Client
elif scenario == "star":
    from aws_lambda_powertools.utilities.auth import *  # noqa: E402,F403

    assert {"JWTVerifier", "OAuth2Client"} <= globals().keys()
else:
    raise ValueError(f"Unknown scenario: {scenario}")
