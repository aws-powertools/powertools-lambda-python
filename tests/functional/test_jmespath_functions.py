# Note: other functions are originally tested in other utilities
# e.g. idempotency, validation, parser, etc.
import hashlib

from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope


def test_sha256():
    # GIVEN
    payload = {"body": "c2FtcGxlIHRpbnkgYmluYXJ5IGNvbnRlbnQ="}
    expected_digest = hashlib.sha256(payload["body"].encode()).hexdigest()

    # WHEN
    digest = extract_data_from_envelope(data=payload, envelope="powertools_sha256(body)")

    # THEN
    assert digest == expected_digest
