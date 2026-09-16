from __future__ import annotations

import math
import re
import time
from typing import Any

import jwt

from aws_lambda_powertools.utilities.auth._base import Verifier
from aws_lambda_powertools.utilities.auth._deadline import Deadline
from aws_lambda_powertools.utilities.auth._errors import sanitize_errors
from aws_lambda_powertools.utilities.auth._jwks import copy_key_set, shared_cache, signing_key
from aws_lambda_powertools.utilities.auth._validation import finite_seconds, https_url, is_nonempty_string, string_list
from aws_lambda_powertools.utilities.auth.exceptions import (
    InvalidClaimsError,
    InvalidSignatureError,
    InvalidTokenError,
    TokenExpiredError,
)

_ASYMMETRIC_ALGORITHMS = frozenset(
    {"RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512", "ES256K", "EdDSA"},
)


class JWTVerifier(Verifier):
    """Verify JWT access tokens for a configured issuer and resource audience.

    Parameters
    ----------
    issuer : str
        Exact trusted HTTPS issuer. Discovery must advertise this issuer.
    audience : str | list[str]
        Accepted resource audiences; at least one must match the token.
    algorithms : list[str]
        Explicit allowlist of asymmetric signing algorithms.
    jwks : dict, optional
        Static key-set snapshot. Its rotation is the application's responsibility.
    jwks_uri : str, optional
        HTTPS key-set endpoint, mutually exclusive with ``jwks``. Without either,
        discover keys from the configured issuer.
    required_claims : list[str], optional
        Claims required in addition to ``iss``, ``aud``, and ``exp``.
    clock_skew_seconds : float
        Nonnegative allowance for temporal claims, by default 60.
    timeout_seconds : float
        Positive discovery/key-fetch and refresh-wait budget, by default 3.
    jwks_max_age_seconds : float
        Positive maximum lifetime of fetched keys, by default 300.
    unknown_kid_cooldown_seconds : float
        Nonnegative interval between unknown-key refreshes, by default 300.

    Raises
    ------
    ValueError
        Configuration is invalid or weakens the required verification profile.

    Examples
    --------
    ```python
    verifier = JWTVerifier(
        issuer="https://idp.example.com/",
        audience="https://orders.example.com",
        algorithms=["RS256"],
        required_claims=["sub"],
    )
    claims = verifier.verify(token)
    ```
    """

    def __init__(
        self,
        *,
        issuer: str,
        audience: str | list[str],
        algorithms: list[str],
        jwks: dict[str, Any] | None = None,
        jwks_uri: str | None = None,
        required_claims: list[str] | None = None,
        clock_skew_seconds: float = 60,
        timeout_seconds: float = 3,
        jwks_max_age_seconds: float = 300,
        unknown_kid_cooldown_seconds: float = 300,
    ) -> None:
        self._issuer = https_url(issuer, issuer=True)
        self._audience = string_list([audience] if isinstance(audience, str) else audience, nonempty=True)
        self._algorithms = string_list(algorithms, nonempty=True)
        if not set(self._algorithms) <= _ASYMMETRIC_ALGORITHMS:
            raise ValueError("Only asymmetric JWT signing algorithms are supported")
        if jwks is not None and jwks_uri is not None:
            raise ValueError("jwks and jwks_uri are mutually exclusive")
        self._jwks = copy_key_set(jwks) if jwks is not None else None
        self._jwks_uri = https_url(jwks_uri) if jwks_uri is not None else None
        self._timeout = finite_seconds(timeout_seconds, positive=True)
        max_age = finite_seconds(jwks_max_age_seconds, positive=True)
        cooldown = finite_seconds(unknown_kid_cooldown_seconds)
        self._cache = shared_cache(self._issuer, self._jwks_uri, max_age, cooldown) if jwks is None else None
        additional_claims = string_list(required_claims if required_claims is not None else [])
        self._required_claims = sorted({"iss", "aud", "exp"} | set(additional_claims))
        self._clock_skew = finite_seconds(clock_skew_seconds)
        self._cognito_client_id: str | None = None

    @classmethod
    def cognito(
        cls,
        *,
        user_pool_id: str,
        client_id: str,
        audience: str | list[str],
        **options: Any,
    ) -> JWTVerifier:
        """Verify resource-bound Cognito access tokens, never Cognito ID tokens.

        Additional keyword arguments configure caching, static keys and claim
        requirements in the same way as ``JWTVerifier``.

        Parameters
        ----------
        user_pool_id : str
            Cognito user pool identifier, including its Region.
        client_id : str
            App client identifier required in the ``client_id`` claim.
        audience : str | list[str]
            Resource audience required in ``aud``. Request resource binding
            when obtaining the access token.

        Examples
        --------
        ```python
        verifier = JWTVerifier.cognito(
            user_pool_id="us-east-1_abc123",
            client_id="orders-client",
            audience="https://orders.example.com",
        )
        ```
        """
        if not isinstance(user_pool_id, str) or not re.fullmatch(
            r"[a-z]{2}(?:-[a-z]+)+-\d+_[A-Za-z0-9]+",
            user_pool_id,
        ):
            raise ValueError("A valid Cognito user pool ID is required")
        if not is_nonempty_string(client_id):
            raise ValueError("A nonempty Cognito app client ID is required")
        if {"issuer", "algorithms", "jwks_uri"} & options.keys():
            raise ValueError("Cognito issuer, algorithm and JWKS endpoint cannot be overridden")
        region = user_pool_id.split("_", 1)[0]
        domain = "amazonaws.com.cn" if region.startswith("cn-") else "amazonaws.com"
        issuer = f"https://cognito-idp.{region}.{domain}/{user_pool_id}"
        if options.get("jwks") is None:
            options["jwks_uri"] = issuer + "/.well-known/jwks.json"
        verifier = cls(issuer=issuer, audience=audience, algorithms=["RS256"], **options)
        verifier._cognito_client_id = client_id
        return verifier

    @classmethod
    def any_of(cls, *verifiers: JWTVerifier) -> Verifier:
        """Route an untrusted issuer claim only to explicitly configured verifiers.

        Unknown issuers trigger no discovery. Duplicate issuer configurations
        are rejected. The returned verifier has the same verification,
        middleware, authorizer, and prefetch interface.

        Examples
        --------
        ```python
        combined = JWTVerifier.any_of(corporate_verifier, cognito_verifier)
        claims = combined.verify(token)
        ```
        """
        if not verifiers or any(not isinstance(verifier, JWTVerifier) for verifier in verifiers):
            raise ValueError("At least one issuer-specific JWTVerifier is required")
        issuers = {verifier._issuer: verifier for verifier in verifiers}
        if len(issuers) != len(verifiers):
            raise ValueError("Duplicate issuer configurations are ambiguous")
        return _IssuerVerifier(issuers)

    def __repr__(self) -> str:
        return "<JWTVerifier>"

    @sanitize_errors
    def prefetch(self) -> None:
        """Populate an absent or expired remote key set; static keys need no I/O.

        Raises
        ------
        JWKSFetchError
            Trusted keys could not be fetched within the configured budget.

        Examples
        --------
        ```python
        verifier.prefetch()  # Optional initialization work outside the handler.
        ```
        """
        if self._cache is not None:
            self._cache.get_keys(None, Deadline(self._timeout))

    @sanitize_errors
    def verify(self, token: str) -> dict[str, Any]:
        """Return verified access-token claims.

        Parameters
        ----------
        token : str
            JWT access token without the ``Bearer`` prefix.

        Returns
        -------
        dict[str, Any]
            Claims after signature, issuer, resource, and time validation.

        Raises
        ------
        InvalidTokenError
            Token, key, signature, or required claims are invalid.
        JWKSFetchError
            Current trusted keys could not be obtained.

        Examples
        --------
        ```python
        claims = verifier.verify(token)
        subject = claims["sub"]
        ```
        """
        header = self._header(token)
        key = self._signing_key(header)
        try:
            claims = jwt.decode(
                token,
                key.key,
                algorithms=self._algorithms,
                issuer=self._issuer,
                audience=self._audience,
                options={
                    "require": self._required_claims,
                    "verify_exp": False,
                    "verify_nbf": False,
                    "verify_iat": False,
                },
            )
        except jwt.InvalidSignatureError:
            raise InvalidSignatureError() from None
        except (jwt.PyJWTError, TypeError, ValueError, OverflowError, RecursionError):
            raise InvalidClaimsError() from None
        self._validate_times(claims)
        if self._cognito_client_id is not None:
            if claims.get("token_use") != "access" or claims.get("client_id") != self._cognito_client_id:
                raise InvalidClaimsError()
        return claims

    def _header(self, token: str) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise InvalidTokenError()
        try:
            header = jwt.get_unverified_header(token)
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise InvalidTokenError() from None
        if (
            header.get("alg") not in self._algorithms
            or not isinstance(header.get("kid"), str)
            or not header["kid"]
            or header.get("crit")
            or header.get("b64") is False
        ):
            raise InvalidTokenError()
        return header

    def _signing_key(self, header: dict[str, Any]) -> jwt.PyJWK:
        keys = self._cache.get_keys(header["kid"], Deadline(self._timeout)) if self._cache is not None else self._jwks
        if keys is None:
            raise InvalidTokenError()
        return signing_key(keys, header)

    def _validate_times(self, claims: dict[str, Any]) -> None:
        for name in ("exp", "nbf", "iat"):
            if name not in claims:
                continue
            value = claims[name]
            try:
                valid = type(value) in (int, float) and math.isfinite(value)
            except OverflowError:
                valid = False
            if not valid:
                raise InvalidClaimsError()
        now = time.time()
        if claims["exp"] <= now - self._clock_skew:
            raise TokenExpiredError()
        if claims.get("nbf", 0) > now + self._clock_skew or claims.get("iat", 0) > now + self._clock_skew:
            raise InvalidClaimsError()


class _IssuerVerifier(Verifier):
    def __init__(self, issuers: dict[str, JWTVerifier]) -> None:
        self._issuers = issuers

    def __repr__(self) -> str:
        return "<JWTVerifier issuer group>"

    @sanitize_errors
    def verify(self, token: str) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise InvalidTokenError()
        try:
            # This payload selects a configured verifier. No unverified claim
            # is returned to callers or used to discover another provider.
            payload = jwt.decode(token, options={"verify_signature": False})
            issuer = payload.get("iss")
        except (jwt.PyJWTError, ValueError, TypeError, RecursionError):
            raise InvalidTokenError() from None
        if not isinstance(issuer, str) or issuer not in self._issuers:
            raise InvalidTokenError()
        return self._issuers[issuer].verify(token)

    @sanitize_errors
    def prefetch(self) -> None:
        for verifier in self._issuers.values():
            verifier.prefetch()
