"""Helpers for application tests that intentionally bypass token verification."""

from __future__ import annotations

import copy
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

if TYPE_CHECKING:
    from collections.abc import Iterator

    from aws_lambda_powertools.utilities.auth._base import Verifier


@contextmanager
def mock_claims(verifier: Verifier, claims: dict[str, Any]) -> Iterator[None]:
    """Temporarily return supplied claims without cryptography or network calls.

    This helper bypasses the verifier's security checks. Use it only in
    application tests; retain separate tests for real token verification.

    Examples
    --------
    ```python
    with mock_claims(verifier, {"sub": "test-user", "scope": "orders:read"}):
        response = app.resolve(event, context)
    ```
    """
    snapshot = copy.deepcopy(claims)
    with patch.object(verifier, "verify", side_effect=lambda token: copy.deepcopy(snapshot)):
        yield
