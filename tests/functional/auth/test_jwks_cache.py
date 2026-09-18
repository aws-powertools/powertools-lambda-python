import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import InvalidTokenError, JWKSFetchError

JWKS_URL = "https://idp.example.com/keys"
ISSUER = "https://idp.example.com/"


def verifier(**options):
    return JWTVerifier(issuer=ISSUER, audience="https://api.example.com", algorithms=["RS256"], **options)


def test_fetch_keys_once_and_reuse_for_warm_invocations(http, jwks, issue_token):
    http.serve(JWKS_URL, jwks)
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://api.example.com",
        algorithms=["RS256"],
        jwks_uri=JWKS_URL,
    )

    assert verifier.verify(issue_token())["sub"] == "user-123"
    assert verifier.verify(issue_token())["sub"] == "user-123"
    assert len(http.requests) == 1


def test_known_keys_are_removed_after_the_key_set_expires(http, jwks, issue_token, clock):
    http.serve(JWKS_URL, jwks)
    subject = verifier(jwks_uri=JWKS_URL)
    subject.verify(issue_token())
    http.serve(JWKS_URL, {"keys": []})
    clock.advance(300)

    with pytest.raises(InvalidTokenError):
        subject.verify(issue_token())
    assert len(http.requests) == 2


def test_refresh_failure_cannot_extend_key_trust_and_uses_backoff(http, jwks, issue_token, clock):
    http.serve(JWKS_URL, jwks)
    subject = verifier(jwks_uri=JWKS_URL)
    subject.verify(issue_token())
    clock.advance(300)
    http.serve(JWKS_URL, {"error": "unavailable"}, status=503)

    for _ in range(3):
        with pytest.raises(JWKSFetchError):
            subject.verify(issue_token())
    assert len(http.requests) == 2

    clock.advance(1)
    http.serve(JWKS_URL, jwks)
    assert subject.verify(issue_token())["sub"] == "user-123"
    assert len(http.requests) == 3


def test_unknown_key_refresh_is_rate_limited_separately_from_freshness(http, jwks, issue_token, clock):
    http.serve(JWKS_URL, jwks)
    subject = verifier(jwks_uri=JWKS_URL, jwks_max_age_seconds=3000, unknown_kid_cooldown_seconds=5)
    subject.verify(issue_token())

    with pytest.raises(InvalidTokenError):
        subject.verify(issue_token(kid="new-key"))
    assert len(http.requests) == 1

    clock.advance(5)
    http.serve(JWKS_URL, {"keys": [{**jwks["keys"][0], "kid": "new-key"}]})
    assert subject.verify(issue_token(kid="new-key"))["sub"] == "user-123"
    with pytest.raises(InvalidTokenError):
        subject.verify(issue_token())
    assert len(http.requests) == 2


def test_unknown_key_cooldown_does_not_prevent_age_required_refresh(http, jwks, issue_token, clock):
    http.serve(JWKS_URL, jwks)
    subject = verifier(jwks_uri=JWKS_URL, jwks_max_age_seconds=2, unknown_kid_cooldown_seconds=300)
    subject.verify(issue_token())
    clock.advance(2)
    http.serve(JWKS_URL, {"keys": []})

    with pytest.raises(InvalidTokenError):
        subject.verify(issue_token())
    assert len(http.requests) == 2


def test_prefetch_does_not_reset_key_age_without_a_fetch(http, jwks, issue_token, clock):
    http.serve(JWKS_URL, jwks)
    subject = verifier(jwks_uri=JWKS_URL)
    subject.prefetch()
    clock.advance(299)
    subject.prefetch()
    http.serve(JWKS_URL, {"keys": []})
    clock.advance(1)

    with pytest.raises(InvalidTokenError):
        subject.verify(issue_token())
    assert len(http.requests) == 2


def test_discovery_validates_issuer_before_retrieving_keys(http, jwks, issue_token):
    http.serve(ISSUER + ".well-known/openid-configuration", {"issuer": ISSUER, "jwks_uri": JWKS_URL})
    http.serve(JWKS_URL, jwks)

    assert verifier().verify(issue_token())["sub"] == "user-123"
    assert [request[1] for request in http.requests] == [ISSUER + ".well-known/openid-configuration", JWKS_URL]


@pytest.mark.parametrize(
    "metadata",
    [
        {"issuer": "https://other.example.com/", "jwks_uri": JWKS_URL},
        {"issuer": ISSUER, "jwks_uri": "http://idp.example.com/keys"},
        {"jwks_uri": JWKS_URL},
        {"issuer": ISSUER},
    ],
)
def test_invalid_discovery_never_falls_back_or_fetches_untrusted_keys(http, issue_token, metadata):
    http.serve(ISSUER + ".well-known/openid-configuration", metadata)

    with pytest.raises(JWKSFetchError):
        verifier().verify(issue_token())
    assert len(http.requests) == 1


@pytest.mark.parametrize(
    "body",
    [{}, {"keys": None}, {"keys": ["bad-key"]}, [], None, b"not json", b"x" * (1024 * 1024 + 1)],
)
def test_malformed_key_sets_fail_closed(http, issue_token, body):
    http.serve(JWKS_URL, body)

    with pytest.raises(JWKSFetchError):
        verifier(jwks_uri=JWKS_URL).verify(issue_token())


def test_concurrent_requests_share_one_key_fetch(http, jwks, issue_token):
    entered = threading.Event()
    release = threading.Event()

    def fetch():
        entered.set()
        assert release.wait(2)
        return jwks

    http.serve(JWKS_URL, fetch)
    subject = verifier(jwks_uri=JWKS_URL)
    token = issue_token()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = [executor.submit(subject.verify, token) for _ in range(8)]
        assert entered.wait(2)
        release.set()
        assert all(result.result(timeout=2)["sub"] == "user-123" for result in results)
    assert len(http.requests) == 1


def test_verifiers_for_the_same_issuer_and_key_source_share_refresh(http, jwks, issue_token):
    http.serve(JWKS_URL, jwks)
    first = verifier(jwks_uri=JWKS_URL)
    second = verifier(jwks_uri=JWKS_URL)

    first.verify(issue_token())
    second.verify(issue_token())
    assert len(http.requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["initial", "expiry", "unknown-key"])
async def test_thread_adapter_keeps_the_event_loop_responsive_during_fetch(http, jwks, issue_token, clock, reason):
    entered = threading.Event()
    release = threading.Event()
    subject = verifier(jwks_uri=JWKS_URL, jwks_max_age_seconds=300, unknown_kid_cooldown_seconds=1)
    kid = "key-1"
    if reason != "initial":
        http.serve(JWKS_URL, jwks)
        subject.prefetch()
        clock.advance(300 if reason == "expiry" else 1)
    if reason == "unknown-key":
        kid = "new-key"
        jwks["keys"][0]["kid"] = kid

    def fetch():
        entered.set()
        assert release.wait(2)
        return jwks

    http.serve(JWKS_URL, fetch)
    verifications = [asyncio.create_task(asyncio.to_thread(subject.verify, issue_token(kid=kid))) for _ in range(3)]
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        await asyncio.sleep(0)
        assert not any(task.done() for task in verifications)
    finally:
        release.set()
    assert all(claims["sub"] == "user-123" for claims in await asyncio.gather(*verifications))
    assert len(http.requests) == (1 if reason == "initial" else 2)
    assert 0 < http.requests[-1][2]["timeout"].total <= 3


def test_failed_unknown_key_refresh_preserves_only_still_fresh_keys(http, jwks, issue_token, clock):
    subject = verifier(jwks_uri=JWKS_URL, unknown_kid_cooldown_seconds=1)
    http.serve(JWKS_URL, jwks)
    subject.prefetch()
    clock.advance(1)
    http.serve(JWKS_URL, {}, status=503)

    with pytest.raises(JWKSFetchError):
        subject.verify(issue_token(kid="new-key"))
    assert subject.verify(issue_token())["sub"] == "user-123"
    assert len(http.requests) == 2

    clock.advance(299)
    with pytest.raises(JWKSFetchError):
        subject.verify(issue_token())


def test_waiting_verifier_timeout_does_not_cancel_the_shared_key_fetch(http, jwks, issue_token):
    entered = threading.Event()
    release = threading.Event()

    def fetch():
        entered.set()
        assert release.wait(5)
        return jwks

    http.serve(JWKS_URL, fetch)
    owner = verifier(jwks_uri=JWKS_URL, timeout_seconds=5)
    waiter = verifier(jwks_uri=JWKS_URL, timeout_seconds=0.1)
    token = issue_token()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(owner.verify, token)
        try:
            assert entered.wait(5)
            with pytest.raises(JWKSFetchError) as error:
                waiter.verify(token)
            assert error.value.__context__ is None
            assert not result.done()
        finally:
            release.set()
        assert result.result(timeout=5)["sub"] == "user-123"

    assert waiter.verify(token)["sub"] == "user-123"
    assert len(http.requests) == 1
