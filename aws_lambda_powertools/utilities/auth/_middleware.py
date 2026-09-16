from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler import ApiGatewayResolver, Response
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler
from aws_lambda_powertools.utilities.auth._authorization import (
    ForbiddenError,
    InsufficientScopeError,
    MissingTokenError,
    enforce_scopes,
    header_token,
    required_scopes,
)
from aws_lambda_powertools.utilities.auth.exceptions import AuthError, InvalidTokenError

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
    from aws_lambda_powertools.utilities.auth._base import Verifier


@dataclass(frozen=True)
class AuthErrorContext:
    """Mapped HTTP failure available to a route's custom error response callback."""

    status_code: int
    headers: dict[str, str]


class AuthMiddleware(BaseMiddlewareHandler[ApiGatewayResolver]):
    def __init__(
        self,
        verifier: Verifier,
        scopes: list[str] | None,
        authorize: Callable[[dict[str, Any]], bool] | None,
        on_error: Callable[[AuthErrorContext], Response] | None,
    ) -> None:
        self._verifier = verifier
        self._scopes = required_scopes(scopes)
        self._authorize = authorize
        self._on_error = on_error

    def handler(self, app: ApiGatewayResolver, next_middleware: NextMiddleware) -> Response:
        try:
            raw = app.current_event.raw_event
            token = header_token(raw.get("headers"), raw.get("multiValueHeaders"))
            claims = self._verifier.verify(token)
            enforce_scopes(claims, self._scopes)
            if self._authorize is not None and self._authorize(claims) is not True:
                raise ForbiddenError()
        except AuthError as error:
            return self._failure(error)
        app.append_context(claims=claims)
        try:
            return next_middleware(app)
        finally:
            # Resolver cleanup can be skipped when a handler raises. Claims
            # belong to this middleware invocation, including on that path.
            app.context.pop("claims", None)

    def _failure(self, error: AuthError) -> Response:
        if isinstance(error, MissingTokenError):
            context = AuthErrorContext(401, {"WWW-Authenticate": "Bearer"})
        elif isinstance(error, InvalidTokenError):
            context = AuthErrorContext(401, {"WWW-Authenticate": 'Bearer error="invalid_token"'})
        elif isinstance(error, InsufficientScopeError):
            scopes = " ".join(self._scopes)
            context = AuthErrorContext(
                403,
                {"WWW-Authenticate": f'Bearer error="insufficient_scope", scope="{scopes}"'},
            )
        elif isinstance(error, ForbiddenError):
            context = AuthErrorContext(403, {})
        else:
            context = AuthErrorContext(503, {})
        if self._on_error is not None:
            return self._on_error(context)
        messages = {401: "Unauthorized", 403: "Forbidden", 503: "Service Unavailable"}
        return Response(
            status_code=context.status_code,
            content_type="application/json",
            body={"message": messages[context.status_code]},
            headers=context.headers,
        )
