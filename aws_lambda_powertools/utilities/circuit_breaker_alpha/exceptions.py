"""
Circuit Breaker exceptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitInfo


class CircuitBreakerError(Exception):
    """
    Base error class.

    Overrides message/details formatting so the printed exception stays readable.
    See https://github.com/aws-powertools/powertools-lambda-python/issues/1772
    """

    def __init__(self, *args: str | Exception | None):
        self.message = str(args[0]) if args else ""
        self.details = "".join(str(arg) for arg in args[1:]) if args[1:] else None

    def __str__(self):
        """Return all arguments formatted, or the original message."""
        if self.message and self.details:
            return f"{self.message} - ({self.details})"
        return self.message


class CircuitBreakerOpenError(CircuitBreakerError):
    """
    Raised when the circuit is open and no ``on_circuit_open`` callback is registered.

    The rejected request never reached the downstream. The circuit snapshot is attached
    so the caller can decide how to respond.

    Parameters
    ----------
    *args : str | Exception | None
        Standard error message/details.
    circuit : CircuitInfo | None
        Snapshot of the circuit at rejection time.

    Example
    -------
    **Handling an open circuit when no callback is registered**

        try:
            charge(order)
        except CircuitBreakerOpenError as exc:
            logger.warning("rejected by circuit %s", exc.circuit.name)
            return {"statusCode": 202}
    """

    def __init__(self, *args: str | Exception | None, circuit: CircuitInfo | None = None):
        self.circuit = circuit
        super().__init__(*args)


class CircuitBreakerConfigError(CircuitBreakerError):
    """
    Raised when ``CircuitBreakerConfig`` is built with an unsupported combination of
    options (for example, both ``handled_exceptions`` and ``ignored_exceptions``).
    """


class CircuitBreakerPersistenceError(CircuitBreakerError):
    """
    Raised by a persistence backend for an unrecoverable store error on a *write* path
    (persisting a state transition), where there is no safe local fallback.

    Reads never raise this: ``get_state`` fails open (treats the circuit as closed) and
    only logs, so a degraded store can never become the outage the breaker is meant to
    prevent. Custom backends may raise this from their write primitives.
    """
