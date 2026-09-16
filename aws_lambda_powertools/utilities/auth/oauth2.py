from __future__ import annotations

import base64
import re
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from urllib.parse import quote_plus, urlencode

import urllib3

from aws_lambda_powertools.utilities.auth._authorization import required_scopes
from aws_lambda_powertools.utilities.auth._errors import sanitize_errors
from aws_lambda_powertools.utilities.auth._http import Deadline, HTTPClient, RequestError
from aws_lambda_powertools.utilities.auth._validation import finite_seconds, https_url
from aws_lambda_powertools.utilities.auth.exceptions import AuthError, TokenExchangeError

if TYPE_CHECKING:
    from collections.abc import Callable

_BEARER_TOKEN = re.compile(r"[-A-Za-z0-9._~+/]+=*")


@dataclass(frozen=True)
class _AccessToken:
    value: str = field(repr=False)
    expires_at: float | None

    def cacheable(self) -> bool:
        return self.expires_at is not None and time.monotonic() < self.expires_at - 30

    def usable(self) -> bool:
        return self.expires_at is None or time.monotonic() < self.expires_at


@dataclass
class _Exchange:
    done: threading.Event = field(default_factory=threading.Event, repr=False)
    token: _AccessToken | None = field(default=None, repr=False)


class OAuth2Client:
    """Acquire bearer tokens using client credentials for one configured resource.

    Parameters
    ----------
    token_url : str
        Trusted HTTPS OAuth token endpoint.
    client_id : str
        Identifier for a client supporting ``client_secret_basic``.
    client_secret : str | Callable[[], str]
        Secret or loader invoked for each exchange attempt.
    scopes : list[str], optional
        Scopes requested on every exchange.
    audience : str, optional
        Provider-specific audience request field, mutually exclusive with resource.
    resource : str, optional
        RFC 8707 resource request field, mutually exclusive with audience.
    timeout_seconds : float
        Positive acquisition budget including retries, by default 3.

    Notes
    -----
    Instances do not share tokens. Tokens are reacquired 30 seconds before
    expiration. Short-lived tokens and tokens without a lifetime are not cached.
    Configure timeouts on application-provided secret loaders.

    Examples
    --------
    ```python
    client = OAuth2Client(
        token_url="https://idp.example.com/token",
        client_id="orders",
        client_secret=load_secret,
        resource="https://inventory.example.com",
        scopes=["inventory:read"],
    )
    headers = client.auth_headers()
    ```
    """

    def __init__(
        self,
        *,
        token_url: str,
        client_id: str,
        client_secret: str | Callable[[], str],
        scopes: list[str] | None = None,
        audience: str | None = None,
        resource: str | None = None,
        timeout_seconds: float = 3,
    ) -> None:
        self._token_url = https_url(token_url)
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError("A nonempty OAuth client ID is required")
        if not callable(client_secret) and (not isinstance(client_secret, str) or not client_secret):
            raise ValueError("client_secret must be a nonempty string or a callable")
        if audience is not None and resource is not None:
            raise ValueError("audience and resource are mutually exclusive")
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = required_scopes(scopes)
        self._timeout = finite_seconds(timeout_seconds, positive=True)
        self._fields = {"grant_type": "client_credentials"}
        if self._scopes:
            self._fields["scope"] = " ".join(self._scopes)
        for name, value in (("audience", audience), ("resource", resource)):
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("Resource selection must be a nonempty string")
                self._fields[name] = value
        self._http = HTTPClient()
        self._cached_token: _AccessToken | None = None
        self._flight: _Exchange | None = None
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return "<OAuth2Client>"

    @sanitize_errors
    def auth_headers(self) -> dict[str, str]:
        """Return an Authorization header for this client's configured resource.

        Raises
        ------
        TokenExchangeError
            A usable bearer token could not be obtained within the budget.

        Examples
        --------
        ```python
        headers = client.auth_headers()
        response = http.request("GET", trusted_inventory_url, headers=headers)
        ```
        """
        try:
            token = self._get_token(Deadline(self._timeout))
        except RequestError:
            raise TokenExchangeError() from None
        return {"Authorization": f"Bearer {token.value}"}

    @sanitize_errors
    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float = 5,
        headers: Mapping[str, str] | None = None,
        **options: Any,
    ) -> urllib3.response.BaseHTTPResponse:
        """Send a synchronous HTTPS request using this resource's bearer token.

        Only trusted destination URLs should be supplied. Redirects and retries
        are disabled, and an existing Authorization header is rejected.
        ``body``, ``fields``, ``json``, ``encode_multipart`` and
        ``multipart_boundary`` are forwarded to urllib3.

        Parameters
        ----------
        method : str
            HTTP method.
        url : str
            Trusted HTTPS destination for this resource's credentials.
        timeout : float
            Positive downstream timeout, separate from acquisition, by default 5.
        headers : Mapping[str, str], optional
            Additional headers, excluding Authorization.

        Returns
        -------
        urllib3.response.BaseHTTPResponse
            Downstream response; inspect its status before consuming its body.

        Raises
        ------
        TokenExchangeError
            Token acquisition failed.
        AuthError
            Downstream transport failed.
        ValueError
            Request configuration is invalid.

        Examples
        --------
        ```python
        response = client.request("GET", "https://inventory.example.com/items")
        if response.status == 200:
            items = response.json()
        ```
        """
        target = https_url(url)
        duration = finite_seconds(timeout, positive=True)
        allowed = {"body", "fields", "json", "encode_multipart", "multipart_boundary"}
        if not options.keys() <= allowed:
            raise ValueError("Unsupported authenticated request option")
        if not isinstance(method, str) or not re.fullmatch(r"[A-Za-z]+", method):
            raise ValueError("A valid HTTP method is required")
        request_headers = self._request_headers(headers)
        request_headers.update(self.auth_headers())
        deadline = Deadline(duration)
        try:
            response = self._http.pool.request(
                method.upper(),
                target,
                headers=request_headers,
                timeout=urllib3.Timeout(total=deadline.remaining()),
                redirect=False,
                retries=False,
                **options,
            )
            deadline.remaining()
            return response
        except (urllib3.exceptions.HTTPError, OSError, ValueError, TypeError, RequestError):
            raise AuthError() from None

    @staticmethod
    def _request_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
        if headers is None:
            return {}
        if not isinstance(headers, Mapping):
            raise ValueError("Request headers must be a mapping of strings")
        for name, value in headers.items():
            if (
                not isinstance(name, str)
                or not isinstance(value, str)
                or name.lower() == "authorization"
                or any(character in name + value for character in ("\r", "\n"))
            ):
                raise ValueError("Request headers must be valid and must not include Authorization")
        return dict(headers)

    def _get_token(self, deadline: Deadline) -> _AccessToken:
        with self._lock:
            if self._cached_token is not None and self._cached_token.cacheable():
                return self._cached_token
            self._cached_token = None
            owner = self._flight is None
            if self._flight is None:
                self._flight = _Exchange()
            flight = self._flight
        if owner:
            self._run_exchange(flight, deadline)
        elif not flight.done.wait(timeout=deadline.remaining()):
            raise TokenExchangeError()
        deadline.remaining()
        if flight.token is None or not flight.token.usable():
            raise TokenExchangeError()
        return flight.token

    def _run_exchange(self, flight: _Exchange, deadline: Deadline) -> None:
        try:
            token = self._exchange(deadline)
            with self._lock:
                if token.cacheable():
                    self._cached_token = token
                flight.token = token
        finally:
            # Waiters keep this flight's result, including uncacheable short
            # tokens. Calls starting after completion must acquire their own.
            with self._lock:
                self._flight = None
                flight.done.set()

    def _exchange(self, deadline: Deadline) -> _AccessToken:
        for attempt in range(3):
            try:
                return self._exchange_once(deadline)
            except RequestError as error:
                if not error.retryable or attempt == 2:
                    raise TokenExchangeError() from None
                delay = 0.1 * 2**attempt
                if deadline.remaining() <= delay:
                    raise TokenExchangeError() from None
                time.sleep(delay)
        raise TokenExchangeError()

    def _credentials(self) -> str:
        try:
            secret = self._client_secret if isinstance(self._client_secret, str) else self._client_secret()
        except Exception:
            # Secret providers can raise arbitrary exceptions containing their
            # configuration or response data. None of it crosses this boundary.
            raise TokenExchangeError() from None
        if not isinstance(secret, str) or not secret:
            raise TokenExchangeError()
        credentials = f"{quote_plus(self._client_id)}:{quote_plus(secret)}"
        return base64.b64encode(credentials.encode()).decode()

    def _exchange_once(self, deadline: Deadline) -> _AccessToken:
        started = time.monotonic()
        authorization = self._credentials()
        status, payload = self._http.json_request(
            "POST",
            self._token_url,
            deadline,
            body=urlencode(self._fields).encode(),
            headers={
                "Authorization": f"Basic {authorization}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if status != 200:
            raise RequestError(retryable=status == 429 or 500 <= status <= 599)
        return self._parse_token(payload, started)

    @staticmethod
    def _parse_token(payload: dict[str, Any], started: float) -> _AccessToken:
        value = payload.get("access_token")
        token_type = payload.get("token_type")
        if (
            not isinstance(value, str)
            or not _BEARER_TOKEN.fullmatch(value)
            or not isinstance(token_type, str)
            or token_type.lower() != "bearer"
        ):
            raise TokenExchangeError()
        expires_at = None
        if "expires_in" in payload:
            try:
                lifetime = finite_seconds(payload["expires_in"], positive=True)
            except ValueError:
                raise TokenExchangeError() from None
            expires_at = started + lifetime
        token = _AccessToken(value, expires_at)
        if not token.usable():
            raise TokenExchangeError()
        return token
