import pytest

from aws_lambda_powertools.utilities.auth.signer.exceptions import SignerConfigError

awscrt = pytest.importorskip("awscrt", reason="SigV4a needs the auth-sigv4a extra")


def test_sigv4a_signs_for_a_region_set(lambda_env, frozen_clock):
    from aws_lambda_powertools.utilities.auth import SigV4aSigner

    # GIVEN a SigV4a signer for two regions
    signer = SigV4aSigner(service="s3", region_set=["us-east-1", "eu-west-1"])

    # WHEN signing an S3 Multi-Region Access Point style request
    signed = signer.sign("GET", "https://mrap-alias.accesspoint.s3-global.amazonaws.com/report.csv")

    # THEN the signature is ECDSA and names the region set
    assert signed.headers["Authorization"].startswith("AWS4-ECDSA-P256-SHA256 Credential=AKIAEXAMPLE/")
    assert signed.headers["X-Amz-Region-Set"] == "us-east-1,eu-west-1"
    assert "x-amz-content-sha256" in {k.lower() for k in signed.headers}


def test_sigv4a_defaults_to_every_region(lambda_env, frozen_clock):
    from aws_lambda_powertools.utilities.auth import SigV4aSigner

    signed = SigV4aSigner(service="execute-api").sign("GET", "https://abc.execute-api.us-east-1.amazonaws.com/p")
    assert signed.headers["X-Amz-Region-Set"] == "*"


def test_sigv4a_rejects_an_empty_region_set(lambda_env):
    from aws_lambda_powertools.utilities.auth import SigV4aSigner

    with pytest.raises(SignerConfigError, match="region_set cannot be empty"):
        SigV4aSigner(service="execute-api", region_set=[])
