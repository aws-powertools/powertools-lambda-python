from __future__ import annotations

import copy
import threading
import time
import weakref
from typing import Any

import jwt

from aws_lambda_powertools.utilities.auth._deadline import Deadline, RequestError
from aws_lambda_powertools.utilities.auth._validation import https_url
from aws_lambda_powertools.utilities.auth.exceptions import InvalidTokenError, JWKSFetchError


def copy_key_set(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("keys"), list):
        raise ValueError("JWKS must contain a keys array")
    if any(not isinstance(key, dict) for key in value["keys"]):
        raise ValueError("JWKS keys must be objects")
    return copy.deepcopy(value)


def signing_key(keys: dict[str, Any], header: dict[str, Any]) -> jwt.PyJWK:
    """Select one verification key, respecting provider-supplied restrictions."""
    matches = [key for key in keys["keys"] if _matches(key, header)]
    if len(matches) != 1:
        raise InvalidTokenError()
    try:
        return jwt.PyJWK.from_dict(matches[0], algorithm=header["alg"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise InvalidTokenError() from None


def _matches(key: dict[str, Any], header: dict[str, Any]) -> bool:
    return (
        key.get("kid") == header["kid"]
        and key.get("kty") in ("RSA", "EC", "OKP")
        and key.get("alg") in (None, header["alg"])
        and key.get("use") in (None, "sig")
        and ("key_ops" not in key or isinstance(key["key_ops"], list) and "verify" in key["key_ops"])
    )


class JWKSCache:
    """A key-set snapshot whose maximum age is independent of miss throttling."""

    def __init__(self, issuer: str, uri: str | None, max_age: float, cooldown: float) -> None:
        from aws_lambda_powertools.utilities.auth._http import HTTPClient

        self._issuer = issuer
        self._uri = uri
        self._max_age = max_age
        self._cooldown = cooldown
        self._http = HTTPClient()
        self._condition = threading.Condition()
        self._keys: dict[str, Any] | None = None
        self._expires_at = 0.0
        self._next_unknown_refresh = 0.0
        self._retry_at = 0.0
        self._failures = 0
        self._refreshing = False

    def get_keys(self, kid: str | None, deadline: Deadline) -> dict[str, Any]:
        try:
            return self._get_keys(kid, deadline)
        except RequestError:
            raise JWKSFetchError() from None

    def _get_keys(self, kid: str | None, deadline: Deadline) -> dict[str, Any]:
        joined_refresh = False
        with self._condition:
            while True:
                now = time.monotonic()
                fresh = self._keys is not None and now < self._expires_at
                if fresh and self._keys is not None:
                    if kid is None or any(key.get("kid") == kid for key in self._keys["keys"]):
                        return self._keys
                if self._refreshing:
                    self._condition.wait(timeout=deadline.remaining())
                    joined_refresh = True
                    continue
                if fresh and (joined_refresh or now < self._next_unknown_refresh):
                    raise InvalidTokenError()
                if now < self._retry_at:
                    raise JWKSFetchError()
                deadline.remaining()
                self._refreshing = True
                self._next_unknown_refresh = now + self._cooldown
                break
        return self._refresh(deadline)

    def _refresh(self, deadline: Deadline) -> dict[str, Any]:
        try:
            keys = self._fetch(deadline)
            deadline.remaining()
            with self._condition:
                # Replacement discards every previously published key. There is
                # deliberately no independent, indefinitely lived per-key cache.
                self._keys = keys
                self._expires_at = time.monotonic() + self._max_age
                self._retry_at = 0.0
                self._failures = 0
            return keys
        except (RequestError, ValueError, TypeError, KeyError):
            with self._condition:
                self._retry_at = time.monotonic() + min(2**self._failures, 30)
                self._failures = min(self._failures + 1, 5)
            raise JWKSFetchError() from None
        finally:
            with self._condition:
                self._refreshing = False
                self._condition.notify_all()

    def _fetch(self, deadline: Deadline) -> dict[str, Any]:
        uri = self._uri
        if uri is None:
            discovery = self._issuer.rstrip("/") + "/.well-known/openid-configuration"
            status, metadata = self._http.json_request("GET", discovery, deadline)
            if status != 200 or metadata.get("issuer") != self._issuer:
                raise RequestError()
            uri = https_url(metadata["jwks_uri"])
        status, data = self._http.json_request("GET", uri, deadline)
        if status != 200:
            raise RequestError()
        return copy_key_set(data)


_caches: weakref.WeakValueDictionary[tuple[str, str | None, float, float], JWKSCache] = weakref.WeakValueDictionary()
_cache_lock = threading.Lock()


def shared_cache(issuer: str, uri: str | None, max_age: float, cooldown: float) -> JWKSCache:
    """Share compatible key caches while at least one verifier uses them."""
    identity = (issuer, uri, max_age, cooldown)
    with _cache_lock:
        cache = _caches.get(identity)
        if cache is None:
            cache = JWKSCache(issuer, uri, max_age, cooldown)
            _caches[identity] = cache
        return cache
