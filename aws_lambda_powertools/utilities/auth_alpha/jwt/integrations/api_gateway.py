from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any, Literal

from aws_lambda_powertools.utilities.auth_alpha._internal.validation import string_list
from aws_lambda_powertools.utilities.auth_alpha.jwt._internal.authorization import (
    ForbiddenError,
    bearer_token,
    enforce_scopes,
    header_token,
    required_scopes,
)
from aws_lambda_powertools.utilities.auth_alpha.jwt.exceptions import AuthError, InvalidClaimsError, InvalidTokenError
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import APIGatewayAuthorizerResponseV2
from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.auth_alpha.jwt._internal.base import Verifier

_ARN = re.compile(r"arn:[a-z0-9-]+:execute-api:[a-z0-9-]+:\d{12}:[a-z0-9]+/[^/]+/[A-Z]+/.*")


def authorize_event(
    verifier: Verifier,
    event: dict[str, Any] | DictWrapper,
    scopes: list[str] | None,
    response_format: Literal["iam", "simple"],
    context_claims: list[str] | None,
    on_error: Callable[[AuthError], None] | None,
) -> dict[str, Any]:
    raw = event.raw_event if isinstance(event, DictWrapper) else event
    _validate_event(raw, response_format)
    arn = _request_arn(raw) if response_format == "iam" else None
    expected = required_scopes(scopes)
    selected = string_list(context_claims if context_claims is not None else [])
    if "claims" in selected:
        raise ValueError("claims is reserved in API Gateway authorizer context")
    claims = _verified_claims(verifier, raw, expected, on_error, require_principal=response_format == "iam")
    context = _context(claims, selected) if claims is not None else {}
    if response_format == "simple":
        return APIGatewayAuthorizerResponseV2(authorize=claims is not None, context=context).asdict()
    return _iam_response(claims, arn, context)


def _validate_event(raw: dict[str, Any], response_format: str) -> None:
    if not isinstance(raw, dict) or raw.get("type") not in ("TOKEN", "REQUEST"):
        raise ValueError("An API Gateway TOKEN or REQUEST authorizer event is required")
    if response_format not in ("iam", "simple"):
        raise ValueError("response_format must be iam or simple")
    if response_format == "simple" and (raw.get("version") != "2.0" or raw["type"] != "REQUEST"):
        raise ValueError("Simple authorizer responses require HTTP API payload version 2.0")


def _verified_claims(
    verifier: Verifier,
    raw: dict[str, Any],
    expected: tuple[str, ...],
    on_error: Callable[[AuthError], None] | None,
    *,
    require_principal: bool,
) -> dict[str, Any] | None:
    try:
        candidate = verifier.verify(_token(raw))
        enforce_scopes(candidate, expected)
        if require_principal:
            _validate_principal(candidate)
        return candidate
    except AuthError as error:
        # The callback observes a public, sanitized error, including failures
        # raised while the caller is already handling another exception.
        error.__context__ = None
        error.__cause__ = None
        if on_error is not None:
            on_error(error)
        if isinstance(error, (InvalidTokenError, ForbiddenError)):
            return None
        raise


def _token(raw: dict[str, Any]) -> str:
    if raw["type"] == "TOKEN":
        return bearer_token(raw.get("authorizationToken"))
    return header_token(raw.get("headers"), raw.get("multiValueHeaders"))


def _validate_principal(claims: dict[str, Any]) -> None:
    if not isinstance(claims.get("sub"), str) or not claims["sub"].strip():
        raise InvalidClaimsError()


def _iam_response(claims: dict[str, Any] | None, arn: str | None, context: dict[str, Any]) -> dict[str, Any]:
    # Preserve the exact supplied resource, including its partition and encoded
    # path. Route builders normalize paths and cannot represent every ARN here.
    result: dict[str, Any] = {
        "principalId": claims["sub"] if claims is not None else "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow" if claims is not None else "Deny",
                    "Resource": [arn],
                },
            ],
        },
    }
    if context:
        result["context"] = context
    return result


def _request_arn(event: dict[str, Any]) -> str:
    arn = event.get("routeArn") if event.get("version") == "2.0" else event.get("methodArn")
    if (
        not isinstance(arn, str)
        or len(arn) > 512
        or not _ARN.fullmatch(arn)
        or any(character in arn for character in ("*", "?", "\r", "\n"))
    ):
        raise ValueError("A concrete API Gateway method or route ARN of at most 512 characters is required")
    return arn


def _context(claims: dict[str, Any], selected: tuple[str, ...]) -> dict[str, Any]:
    context = {}
    for name in selected:
        value = claims.get(name)
        if isinstance(value, (str, bool, int)) or isinstance(value, float) and math.isfinite(value):
            context[name] = value
    return context
