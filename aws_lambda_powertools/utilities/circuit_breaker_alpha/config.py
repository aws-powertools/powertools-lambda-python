"""
Configuration for the Circuit Breaker utility.
"""

from __future__ import annotations

from aws_lambda_powertools.utilities.circuit_breaker_alpha.exceptions import CircuitBreakerConfigError


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
    handled_exceptions : tuple[type[Exception], ...] | None
        Allowlist: only these exception types count as failures; anything else
        propagates without affecting the circuit. Mutually exclusive with
        ``ignored_exceptions``. Defaults to ``None`` (treated as ``(Exception,)``).
    ignored_exceptions : tuple[type[Exception], ...] | None
        Denylist: every exception counts as a failure *except* these. Mutually
        exclusive with ``handled_exceptions``. Defaults to ``None``.
    local_cache_max_age : int
        Seconds a circuit's state is cached in the execution environment before a
        read-through to the store. Matches the Parameters utility default. Defaults to 5.

    Raises
    ------
    CircuitBreakerConfigError
        If both ``handled_exceptions`` and ``ignored_exceptions`` are provided, or a
        numeric tunable is not a positive integer.

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
        handled_exceptions: tuple[type[Exception], ...] | None = None,
        ignored_exceptions: tuple[type[Exception], ...] | None = None,
        local_cache_max_age: int = 5,
    ):
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
