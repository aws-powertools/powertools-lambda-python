from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.event_handler import Response
    from aws_lambda_powertools.utilities.auth._middleware import AuthErrorContext, AuthMiddleware
    from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class Verifier(ABC):
    """Shared verification interface used by issuer-specific and routed verifiers."""

    @abstractmethod
    def verify(self, token: str) -> dict[str, Any]:
        """Return verified claims or raise an Auth utility error."""

    @abstractmethod
    def prefetch(self) -> None:
        """Populate remote key caches without accepting a token."""

    def require(
        self,
        *,
        scopes: list[str] | None = None,
        authorize: Callable[[dict[str, Any]], bool] | None = None,
        on_error: Callable[[AuthErrorContext], Response] | None = None,
    ) -> AuthMiddleware:
        """Create Event Handler middleware enforcing token validity and all scopes.

        Successful verification stores claims in ``app.context["claims"]``
        while the downstream middleware and handler execute. Claims are
        removed when they return or raise.
        Missing/invalid tokens return 401, missing permissions return 403, and
        unavailable signing keys return 503. A custom error callback replaces
        the response, never execution of the protected handler.

        Parameters
        ----------
        scopes : list[str], optional
            Every listed scope must be present in the token.
        authorize : Callable, optional
            Additional policy receiving verified claims; must return True.
        on_error : Callable, optional
            Receives status_code and headers and returns an Event Handler Response.

        Examples
        --------
        ```python
        @app.get("/orders", middlewares=[verifier.require(scopes=["orders:read"])])
        def orders():
            return {"subject": app.context["claims"]["sub"]}
        ```
        """
        from aws_lambda_powertools.utilities.auth._middleware import AuthMiddleware

        return AuthMiddleware(self, scopes, authorize, on_error)

    def authorize(
        self,
        event: dict[str, Any] | DictWrapper,
        *,
        scopes: list[str] | None = None,
        response_format: Literal["iam", "simple"] = "iam",
        context_claims: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return an API Gateway authorizer response for the current request.

        IAM allows require a nonempty ``sub`` and target the supplied ARN only.
        Simple responses require payload version 2.0 and must also be enabled
        in the Gateway deployment. Disable Gateway result caching when each
        request must be verified; this method cannot change Gateway's TTL.

        Parameters
        ----------
        event : dict | DictWrapper
            REST TOKEN/REQUEST or HTTP REQUEST authorizer event.
        scopes : list[str], optional
            Every listed scope must be present in the token.
        response_format : Literal["iam", "simple"]
            Response format configured in Gateway, by default iam.
        context_claims : list[str], optional
            Selected scalar claims to include; no claims are copied by default.

        Examples
        --------
        ```python
        return verifier.authorize(
            event, scopes=["orders:read"], response_format="iam", context_claims=["sub"],
        )
        ```
        """
        from aws_lambda_powertools.utilities.auth._authorizer import authorize_event

        return authorize_event(self, event, scopes, response_format, context_claims)
