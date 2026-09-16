from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from aws_lambda_powertools.utilities.auth.exceptions import AuthError

if TYPE_CHECKING:
    from collections.abc import Callable

_P = ParamSpec("_P")
_T = TypeVar("_T")


def sanitize_errors(operation: Callable[_P, _T]) -> Callable[_P, _T]:
    """Detach provider exceptions before an Auth error leaves a public operation."""

    @wraps(operation)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        try:
            return operation(*args, **kwargs)
        except AuthError as error:
            # `raise ... from None` only suppresses display of the context.
            # Clear both references and use a bare re-raise so Python does not
            # attach the active exception again.
            error.__context__ = None
            error.__cause__ = None
            raise

    return wrapper
