import pytest

from aws_lambda_powertools.utilities.auth import SignedRequest, SigV4Signer
from aws_lambda_powertools.utilities.auth.signer.exceptions import SignerConfigError
from tests.functional.auth.signer.conftest import reference_signature

API_URL = "https://abc123.execute-api.us-east-1.amazonaws.com/prod/orders"


def test_sign_adds_sigv4_headers_matching_the_sdk(lambda_env, frozen_clock):
    # GIVEN a signer configured from the Lambda environment
    signer = SigV4Signer(service="execute-api")

    # WHEN signing a request
    signed = signer.sign("POST", API_URL, headers={"content-type": "application/json"}, body='{"id": "o-1"}')

    # THEN the result is a SignedRequest whose headers match what botocore itself produces
    assert isinstance(signed, SignedRequest)
    assert signed.method == "POST" and signed.url == API_URL and signed.body == b'{"id": "o-1"}'
    expected = reference_signature(
        "POST",
        API_URL,
        {"content-type": "application/json"},
        b'{"id": "o-1"}',
        "execute-api",
        "us-east-1",
    )
    assert signed.headers["Authorization"] == expected["Authorization"]
    assert signed.headers["Authorization"].startswith(
        "AWS4-HMAC-SHA256 Credential=AKIAEXAMPLE/20261115/us-east-1/execute-api/aws4_request",
    )
    assert signed.headers["X-Amz-Date"] == "20261115T120000Z"
    assert signed.headers["X-Amz-Security-Token"] == "tokenexample"  # noqa: S105 test value
    assert signed.headers["content-type"] == "application/json"


def test_sign_keeps_repeated_query_parameters(lambda_env, frozen_clock):
    # GIVEN a URL with a repeated query parameter
    url = f"{API_URL}?status=open&status=paid&limit=5"

    # WHEN signing
    signed = SigV4Signer(service="execute-api").sign("GET", url)

    # THEN both values stay in the URL and the signature is the one the SDK computes for them
    assert signed.url == url
    assert (
        signed.headers["Authorization"]
        == reference_signature("GET", url, {}, None, "execute-api", "us-east-1")["Authorization"]
    )


def test_sign_accepts_str_bytes_and_empty_bodies(lambda_env, frozen_clock):
    signer = SigV4Signer(service="lambda")
    url = "https://fn.lambda-url.us-east-1.on.aws/"

    # GIVEN the same payload as str and as bytes
    as_str = signer.sign("POST", url, body="hello")
    as_bytes = signer.sign("POST", url, body=b"hello")
    empty = signer.sign("GET", url)

    # THEN both sign identically and an empty body still signs
    assert as_str.headers["Authorization"] == as_bytes.headers["Authorization"]
    assert as_str.body == b"hello"
    assert empty.body is None and empty.headers["Authorization"]


def test_s3_requests_follow_s3_canonical_rules(lambda_env, frozen_clock):
    # GIVEN an S3 object key with characters S3 encodes differently from other services
    url = "https://my-bucket.s3.us-east-1.amazonaws.com/reports/2026 11/summary+v2.csv"

    # WHEN signing for s3
    signed = SigV4Signer(service="s3").sign("GET", url)

    # THEN the payload hash header is present and the signature matches botocore's S3 signer, not the generic one
    assert "X-Amz-Content-SHA256" in signed.headers
    assert (
        signed.headers["Authorization"]
        == reference_signature("GET", url, {}, None, "s3", "us-east-1", s3=True)["Authorization"]
    )
    assert (
        signed.headers["Authorization"] != reference_signature("GET", url, {}, None, "s3", "us-east-1")["Authorization"]
    )


def test_explicit_region_wins_over_the_environment(lambda_env, frozen_clock):
    signed = SigV4Signer(service="execute-api", region="eu-west-1").sign("GET", API_URL)
    assert "/eu-west-1/execute-api/aws4_request" in signed.headers["Authorization"]


def test_region_falls_back_to_aws_default_region(lambda_env, monkeypatch):
    monkeypatch.delenv("AWS_REGION")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "sa-east-1")
    assert SigV4Signer(service="execute-api").region == "sa-east-1"


def test_missing_region_fails_at_construction(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secretexample")  # noqa: S105 test value
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    with pytest.raises(SignerConfigError, match="region could not be determined"):
        SigV4Signer(service="execute-api")


def test_missing_credentials_fail_at_construction(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SignerConfigError, match="no credentials in the environment") as exc:
        SigV4Signer(service="execute-api")
    assert exc.value.reason.value == "signer_misconfigured"
    assert "secret" not in str(exc.value).lower().replace("secret_access_key", "")


def test_explicit_credentials_are_used(monkeypatch, frozen_clock):
    from botocore.credentials import Credentials

    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)

    # GIVEN credentials passed explicitly, say for a cross-account call
    signer = SigV4Signer(service="execute-api", region="us-east-1", credentials=Credentials("AKIAOTHER", "othersecret"))
    signed = signer.sign("GET", API_URL)

    # THEN they sign the request and no session token header is added
    assert "Credential=AKIAOTHER/" in signed.headers["Authorization"]
    assert "X-Amz-Security-Token" not in signed.headers


def test_session_credentials_are_used(lambda_env, frozen_clock):
    import botocore.session

    # GIVEN a botocore session (its provider chain reads the same environment here)
    signer = SigV4Signer(service="execute-api", session=botocore.session.get_session())

    # THEN the session's credentials sign the request
    assert "Credential=AKIAEXAMPLE/" in signer.sign("GET", API_URL).headers["Authorization"]


def test_service_is_required(lambda_env):
    with pytest.raises(SignerConfigError, match="service is required"):
        SigV4Signer(service="")


def test_requests_auth_signs_the_prepared_request(lambda_env, frozen_clock):
    requests = pytest.importorskip("requests")

    # GIVEN a requests call using the signer as auth
    prepared = requests.Request(
        "POST",
        API_URL,
        json={"id": "o-1"},
        auth=SigV4Signer(service="execute-api").requests_auth(),
    ).prepare()

    # THEN the prepared request carries the signature computed over the headers requests sends
    assert prepared.headers["Authorization"].startswith("AWS4-HMAC-SHA256")
    expected = reference_signature(
        "POST",
        API_URL,
        {k: v for k, v in prepared.headers.items() if k not in ("Authorization", "X-Amz-Date", "X-Amz-Security-Token")},
        prepared.body,
        "execute-api",
        "us-east-1",
    )
    assert prepared.headers["Authorization"] == expected["Authorization"]


def test_httpx_auth_signs_the_request(lambda_env, frozen_clock):
    httpx = pytest.importorskip("httpx")

    # GIVEN an httpx client using the signer as auth
    signer = SigV4Signer(service="execute-api")
    captured = {}

    def handler(request):
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"ok": True})

    with httpx.Client(transport=httpx.MockTransport(handler), auth=signer.httpx_auth()) as client:
        response = client.post(API_URL, json={"id": "o-1"})

    # THEN the request went out signed
    assert response.status_code == 200
    assert captured["headers"]["authorization"].startswith("AWS4-HMAC-SHA256")
    assert captured["headers"]["x-amz-date"] == "20261115T120000Z"


def test_streaming_bodies_are_rejected(lambda_env):
    import io

    class FakeRequest:
        method = "POST"
        url = API_URL
        headers = {}
        body = io.BytesIO(b"stream")

    with pytest.raises(TypeError, match="streaming request bodies"):
        SigV4Signer(service="execute-api").requests_auth()(FakeRequest())


def test_query_string_is_canonicalised_before_signing(lambda_env, frozen_clock):
    # GIVEN a URL encoded the way HTTP clients do it: + for a space, bare characters, repeated keys
    url = f"{API_URL}?q=a+b%26c&status=open&status=paid&blank="

    # WHEN signing
    signed = SigV4Signer(service="execute-api").sign("GET", url)

    # THEN the URL to send uses SigV4 encoding, keeps every pair, and the signature is computed over that URL
    assert signed.url == f"{API_URL}?q=a%20b%26c&status=open&status=paid&blank="
    assert (
        signed.headers["Authorization"]
        == reference_signature("GET", signed.url, {}, None, "execute-api", "us-east-1")["Authorization"]
    )


def test_requests_auth_sends_the_canonical_url(lambda_env, frozen_clock):
    requests = pytest.importorskip("requests")

    # GIVEN requests encoding a space as +
    prepared = requests.Request(
        "GET",
        API_URL,
        params={"q": "a b"},
        auth=SigV4Signer(service="execute-api").requests_auth(),
    ).prepare()

    # THEN the request that goes out carries the %20 form the signature was computed over
    assert prepared.url == f"{API_URL}?q=a%20b"
    assert (
        prepared.headers["Authorization"]
        == reference_signature(
            "GET",
            prepared.url,
            {
                k: v
                for k, v in prepared.headers.items()
                if k not in ("Authorization", "X-Amz-Date", "X-Amz-Security-Token")
            },
            None,
            "execute-api",
            "us-east-1",
        )["Authorization"]
    )


def test_httpx_auth_sends_the_canonical_url(lambda_env, frozen_clock):
    httpx = pytest.importorskip("httpx")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200)

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        auth=SigV4Signer(service="execute-api").httpx_auth(),
    ) as client:
        client.get(API_URL, params=[("status", "open"), ("status", "paid"), ("q", "a b")])

    assert seen["url"] == f"{API_URL}?status=open&status=paid&q=a%20b"


def test_session_without_credentials_fails_at_construction(lambda_env):
    class EmptySession:
        def get_credentials(self):
            return None

    with pytest.raises(SignerConfigError, match="the session has no credentials"):
        SigV4Signer(service="execute-api", session=EmptySession())


def test_requests_auth_signs_a_text_body(lambda_env, frozen_clock):
    requests = pytest.importorskip("requests")

    # GIVEN a form-style text body, which requests keeps as str
    prepared = requests.Request(
        "POST",
        API_URL,
        data="name=powertools",
        auth=SigV4Signer(service="execute-api").requests_auth(),
    ).prepare()

    # THEN it is signed over the encoded bytes of that text
    expected = reference_signature(
        "POST",
        API_URL,
        {k: v for k, v in prepared.headers.items() if k not in ("Authorization", "X-Amz-Date", "X-Amz-Security-Token")},
        b"name=powertools",
        "execute-api",
        "us-east-1",
    )
    assert prepared.headers["Authorization"] == expected["Authorization"]


def test_signer_package_exposes_only_its_public_names():
    from aws_lambda_powertools.utilities.auth import signer

    assert {"SigV4Signer", "SigV4aSigner", "SignedRequest"} <= set(dir(signer))
    with pytest.raises(AttributeError, match="has no attribute 'unknown'"):
        _ = signer.unknown
