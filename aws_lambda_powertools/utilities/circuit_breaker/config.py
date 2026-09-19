"""
Configuration for the Circuit Breaker utility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.circuit_breaker.exceptions import CircuitBreakerConfigError

if TYPE_CHECKING:
    from collections.abc import Iterable


class CircuitBreakerConfig:
    """
    Tunables for a circuit breaker.

    All values have sensible defaults, so ``CircuitBreakerConfig()`` is a valid
    production configuration. Pass an instance to ``@circuit_breaker(config=...)`` to
    override them.

    Parameters
    ----------
    failure_threshold : int
        Number of *consecutive* failures that trips a closed circuit to open. Defaults to 5.
    recovery_timeout : int
        Seconds the circuit stays open before allowing a half-open probe. Defaults to 30.
    success_threshold : int
        Number of *consecutive* probe successes required to close a half-open circuit.
        Defaults to 3.
    handled_exceptions : type[Exception] | Iterable[type[Exception]] | None
        Allowlist: only these exception types count as failures; anything else
        propagates without affecting the circuit. Accepts a single exception type or
        an iterable of them (normalized to a tuple). Mutually exclusive with
        ``ignored_exceptions``. Defaults to ``None`` (treated as ``(Exception,)``).
    ignored_exceptions : type[Exception] | Iterable[type[Exception]] | None
        Denylist: every exception counts as a failure *except* these. Accepts a single
        exception type or an iterable of them (normalized to a tuple). Mutually
        exclusive with ``handled_exceptions``. Defaults to ``None``.
    local_cache_max_age : int
        Seconds a circuit's state is cached in the execution environment before a
        read-through to the store. Matches the Parameters utility default. Defaults to 5.

    Raises
    ------
    CircuitBreakerConfigError
        If both ``handled_exceptions`` and ``ignored_exceptions`` are provided, a
        numeric tunable is not a positive integer, or an exception allowlist/denylist
        is empty or contains a value that is not an exception type.

    Example
    -------
    **Only count timeouts and connection errors as failures**

        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30,
            handled_exceptions=(TimeoutError, ConnectionError),
        )
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 3,
        handled_exceptions: type[Exception] | Iterable[type[Exception]] | None = None,
        ignored_exceptions: type[Exception] | Iterable[type[Exception]] | None = None,
        local_cache_max_age: int = 5,
    ):
        # Normalize first: a single exception type or any iterable becomes a tuple, and a
        # bad value fails here (at construction) rather than as a cryptic isinstance
        # TypeError later, the first time the circuit evaluates a failure.
        handled_exceptions = self._normalize_exceptions(handled_exceptions, "handled_exceptions")
        ignored_exceptions = self._normalize_exceptions(ignored_exceptions, "ignored_exceptions")

        self._validate(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            handled_exceptions=handled_exceptions,
            ignored_exceptions=ignored_exceptions,
            local_cache_max_age=local_cache_max_age,
        )

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.handled_exceptions = handled_exceptions
        self.ignored_exceptions = ignored_exceptions
        self.local_cache_max_age = local_cache_max_age

    @staticmethod
    def _validate(
        failure_threshold: int,
        recovery_timeout: int,
        success_threshold: int,
        handled_exceptions: tuple[type[Exception], ...] | None,
        ignored_exceptions: tuple[type[Exception], ...] | None,
        local_cache_max_age: int,
    ) -> None:
        if handled_exceptions and ignored_exceptions:
            raise CircuitBreakerConfigError(
                "handled_exceptions and ignored_exceptions are mutually exclusive; pass only one.",
            )

        # Thresholds and timeouts must be strictly positive; cache age may be 0 (always read through).
        for field, value in (
            ("failure_threshold", failure_threshold),
            ("recovery_timeout", recovery_timeout),
            ("success_threshold", success_threshold),
        ):
            if not isinstance(value, int) or value <= 0:
                raise CircuitBreakerConfigError(f"{field} must be a positive integer, got {value!r}.")

        if not isinstance(local_cache_max_age, int) or local_cache_max_age < 0:
            raise CircuitBreakerConfigError(
                f"local_cache_max_age must be a non-negative integer, got {local_cache_max_age!r}.",
            )

    @classmethod
    def _normalize_exceptions(
        cls,
        value: type[Exception] | Iterable[type[Exception]] | None,
        field: str,
    ) -> tuple[type[Exception], ...] | None:
        """Coerce a single exception type or an iterable of them into a validated, non-empty tuple.

        Runs at construction so a bad value fails immediately with a clear error, rather
        than as a cryptic ``isinstance`` ``TypeError`` from ``counts_as_failure`` the
        first time the circuit evaluates a failure (i.e. only once the dependency is
        already unhealthy).
        """
        if value is None:
            return None

        invalid = f"{field} must be an exception type or an iterable of exception types, got {value!r}."
        # A str is iterable; reject it rather than iterate it as a sequence of characters.
        if isinstance(value, str):
            raise CircuitBreakerConfigError(invalid)

        if isinstance(value, type):
            # ty (unlike mypy) does not narrow the union here, so it needs the ignore.
            exceptions: tuple[type[Exception], ...] = (value,)  # ty: ignore[invalid-assignment]
        else:
            try:
                exceptions = tuple(value)
            except TypeError:
                raise CircuitBreakerConfigError(invalid) from None

        cls._validate_exception_types(exceptions, field)
        return exceptions

    @staticmethod
    def _validate_exception_types(exceptions: tuple[type[Exception], ...], field: str) -> None:
        """Require a non-empty tuple whose every element is an exception type."""
        if not exceptions:
            raise CircuitBreakerConfigError(f"{field} must contain at least one exception type.")
        for exception in exceptions:
            if not (isinstance(exception, type) and issubclass(exception, Exception)):
                raise CircuitBreakerConfigError(f"{field} must contain only exception types, got {exception!r}.")

    def counts_as_failure(self, exception: Exception) -> bool:
        """
        Decide whether an exception raised by the protected call counts as a circuit failure.

        Parameters
        ----------
        exception : Exception
            The exception raised by the protected function.

        Returns
        -------
        bool
            ``True`` if the exception should increment the failure counter, ``False`` if
            it should propagate without affecting the circuit.
        """
        if self.handled_exceptions is not None:
            return isinstance(exception, self.handled_exceptions)
        if self.ignored_exceptions is not None:
            return not isinstance(exception, self.ignored_exceptions)
        # Default: any exception counts as a failure.
        return True
