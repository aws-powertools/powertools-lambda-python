from __future__ import annotations

import time

from aws_lambda_powertools.utilities.auth._validation import finite_seconds


class RequestError(Exception):
    """Internal, credential-free transport failure."""

    def __init__(self, *, retryable: bool = False) -> None:
        self.retryable = retryable
        super().__init__("Authentication endpoint request failed")


class Deadline:
    """One monotonic budget shared across a fetch and any subsequent requests."""

    def __init__(self, seconds: float) -> None:
        self._expires_at = time.monotonic() + finite_seconds(seconds, positive=True)

    def remaining(self) -> float:
        remaining = self._expires_at - time.monotonic()
        if remaining <= 0:
            raise RequestError(retryable=True)
        return remaining
