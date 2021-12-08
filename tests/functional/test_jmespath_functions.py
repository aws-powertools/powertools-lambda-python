# Note: other functions are originally tested in other utilities
# e.g. idempotency, validation, parser, etc.
import hashlib

import pytest

from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope


@pytest.mark.parametrize("alg", ["md5", "sha256", "sha512", "sha3_256"])
def test_hash_default_alg(alg):
    # GIVEN
    payload = {"body": "c2FtcGxlIHRpbnkgYmluYXJ5IGNvbnRlbnQ="}
    hasher = getattr(hashlib, alg)
    expected_digest: str = hasher(payload["body"].encode()).hexdigest()

    # WHEN
    digest = extract_data_from_envelope(data=payload, envelope=f"powertools_hash(body, '{alg}')")

    # THEN
    assert digest == expected_digest
