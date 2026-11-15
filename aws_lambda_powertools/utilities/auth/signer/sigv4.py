"""Sign HTTP requests to AWS services with Signature Version 4, using the botocore already in the Lambda runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qsl, quote, urlsplit, urlunsplit

from aws_lambda_powertools.utilities.auth.signer.exceptions import SignerConfigError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from botocore.auth import BaseSigner
    from botocore.credentials import Credentials
    from botocore.session import Session

__all__ = ["SigV4Signer", "SignedRequest"]

_S3_SERVICES = frozenset({"s3", "s3-object-lambda", "s3express"})


@dataclass(frozen=True)
class SignedRequest:
    """A request with its signature headers added. Send it with any HTTP client."""

    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None


class SigV4Signer:
    """Sign HTTP requests with AWS Signature Version 4.

    Signing is separate from sending: ``sign()`` returns the signed headers and URL and never
    touches the network. ``requests_auth()`` and ``httpx_auth()`` plug the same signing into
    those clients so each request is signed on the way out.

    Region and credentials come from the Lambda environment by default. Pass ``credentials``
    or ``session`` to run outside Lambda or to call another account.

    Parameters
    ----------
    service : str
        Signing name of the target service, for example ``execute-api``, ``lambda``, ``appsync``, ``es`` or ``s3``.
    region : str, optional
        Region to sign for. Defaults to ``AWS_REGION``, then ``AWS_DEFAULT_REGION``.
    credentials : botocore.credentials.Credentials, optional
        Explicit credentials. Defaults to the ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY`` and
        ``AWS_SESSION_TOKEN`` environment variables that Lambda sets.
    session : botocore.session.Session, optional
        Resolve credentials through this session's provider chain instead of the environment.

    Example
    -------
    >>> signer = SigV4Signer(service="execute-api")
    >>> signed = signer.sign("GET", "https://abc123.execute-api.us-east-1.amazonaws.com/prod/orders")
    >>> signed.headers["Authorization"].startswith("AWS4-HMAC-SHA256")
    True
    """

    def __init__(
        self,
        service: str,
        *,
        region: str | None = None,
        credentials: Credentials | None = None,
        session: Session | None = None,
    ) -> None:
        if not service:
            raise SignerConfigError("service is required, for example 'execute-api' or 'lambda'")
        self.service = service
        self.region = self._resolve_region(region)
        self._credentials = self._resolve_credentials(credentials, session)

    def sign(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str] | None = None,
        body: str | bytes | None = None,
    ) -> SignedRequest:
        """Sign a request and return it with the signature headers added. No network call is made."""
        from botocore.awsrequest import AWSRequest

        payload = body.encode("utf-8") if isinstance(body, str) else body
        url = _canonical_query(url)
        request = AWSRequest(method=method.upper(), url=url, headers=dict(headers or {}), data=payload)
        self._auth().add_auth(request)
        return SignedRequest(method=method.upper(), url=url, headers=dict(request.headers), body=payload)

    def requests_auth(self) -> Any:
        """Return an ``auth=`` object for the ``requests`` library that signs every request."""
        return _RequestsAuth(self)

    def httpx_auth(self) -> Any:
        """Return an ``auth=`` object for the ``httpx`` library that signs every request."""
        return _HttpxAuth(self)

    def _auth(self) -> BaseSigner:
        from botocore.auth import S3SigV4Auth, SigV4Auth

        auth_class = S3SigV4Auth if self.service in _S3_SERVICES else SigV4Auth
        return auth_class(self._credentials, self.service, self.region)

    @staticmethod
    def _resolve_region(region: str | None) -> str:
        resolved = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if not resolved:
            raise SignerConfigError("region could not be determined; pass region= or set AWS_REGION")
        return resolved

    @staticmethod
    def _resolve_credentials(credentials: Credentials | None, session: Session | None) -> Credentials:
        if credentials is not None:
            return credentials
        if session is not None:
            resolved = session.get_credentials()
            if resolved is None:
                raise SignerConfigError("the session has no credentials")
            return resolved

        from botocore.credentials import Credentials

        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        if not access_key or not secret_key:
            raise SignerConfigError(
                "no credentials in the environment; pass credentials= or session= when running outside Lambda",
            )
        return Credentials(access_key, secret_key, os.getenv("AWS_SESSION_TOKEN") or None)


def _canonical_query(url: str) -> str:
    """Re-encode the query string the way SigV4 canonicalises it, so what is signed is what is sent.

    HTTP clients encode a space as ``+`` and leave some characters bare; the service canonicalises
    with ``%20`` and percent-encodes everything but unreserved characters, and the signatures would
    not match. Repeated keys are kept.
    """
    parts = urlsplit(url)
    if not parts.query:
        return url
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    query = "&".join(f"{quote(key, safe='-_.~')}={quote(value, safe='-_.~')}" for key, value in pairs)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def _read_body(body: Any) -> bytes | None:
    if body is None or isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")
    raise TypeError("streaming request bodies cannot be signed; pass bytes or str")


class _RequestsAuth:
    """Callable accepted by ``requests`` as ``auth=``; signs the prepared request in place."""

    def __init__(self, signer: SigV4Signer) -> None:
        self._signer = signer

    def __call__(self, request: Any) -> Any:
        signed = self._signer.sign(request.method, request.url, dict(request.headers), _read_body(request.body))
        request.url = signed.url
        request.headers.update(signed.headers)
        return request


class _HttpxAuth:
    """Callable accepted by ``httpx`` as ``auth=``; signs the request in place."""

    def __init__(self, signer: SigV4Signer) -> None:
        self._signer = signer

    def __call__(self, request: Any) -> Any:
        signed = self._signer.sign(request.method, str(request.url), dict(request.headers), _read_body(request.content))
        if signed.url != str(request.url):
            request.url = request.url.copy_with(query=urlsplit(signed.url).query.encode())
        for name, value in signed.headers.items():
            request.headers[name] = value
        return request
