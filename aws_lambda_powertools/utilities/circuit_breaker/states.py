"""
Public state types for the Circuit Breaker utility.

These are the only circuit-breaker types handed to user code (callbacks and the
``CircuitInfo`` attached to ``CircuitBreakerOpenError``). They deliberately expose no
persistence internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CircuitState(str, Enum):
    """
    The state of a circuit.

    Subclasses ``str`` so the value serializes directly to a persistence store as a
    plain string (e.g. DynamoDB) and compares equal to its string form.

    Attributes
    ----------
    CLOSED : str
        Normal operation. Requests reach the downstream and failures are counted.
    OPEN : str
        The downstream is considered unhealthy. The protected call is skipped.
    HALF_OPEN : str
        Recovery is being tested. A limited number of probe requests are allowed
        through to decide whether the circuit should close again.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __str__(self) -> str:
        """Return the bare value (e.g. ``"OPEN"``) rather than ``CircuitState.OPEN``."""
        return self.value


@dataclass(frozen=True)
class CircuitInfo:
    """
    Immutable snapshot of a circuit, passed to user code.

    This is the public boundary of the utility: it is the single argument (alongside
    the payload) handed to an ``on_circuit_open`` callback, and it is attached to
    ``CircuitBreakerOpenError`` so a caller can inspect why the circuit rejected the
    request. No persistence details (probe lock, TTL) are exposed.

    Parameters
    ----------
    name : str
        The circuit name, as given to the ``@circuit_breaker`` decorator.
    state : CircuitState
        The circuit state at the moment the request was evaluated.
    failure_count : int
        A point-in-time snapshot of the *consecutive* failures the environment that
        last wrote the record had counted, captured at the moment of a state
        transition. It is **not** a running total of failures across the fleet: the
        failure counter lives in memory per execution environment (so the healthy path
        stays write-free), and only the tripping environment's count is persisted when
        the circuit opens. It is ``0`` in states reached without a fresh trip (for
        example ``HALF_OPEN``, or ``OPEN`` re-entered after a failed probe). For failure
        *volume*, emit a CloudWatch metric from your own code or an ``on_transition``
        hook rather than reading this field.
    opened_at : int | None
        Unix timestamp (seconds) at which the circuit opened, or ``None`` while the
        circuit is closed. Drives the recovery timeout.

    Example
    -------
    **Inspecting circuit details inside a callback**

        def on_open(payload: dict, circuit: CircuitInfo):
            logger.warning("circuit %s open since %s", circuit.name, circuit.opened_at)
            return {"statusCode": 503}
    """

    name: str
    state: CircuitState
    failure_count: int
    opened_at: int | None = None


@dataclass(frozen=True)
class CircuitTransition:
    """
    Immutable description of a circuit state change, passed to an ``on_transition`` hook.

    The hook fires only on the rare state transitions a circuit makes (open, probe,
    close, reopen), never on the per-invocation hot path, so emitting a metric from it
    does not undermine the write-free healthy path.

    Parameters
    ----------
    circuit_name : str
        The circuit name, as given to the ``@circuit_breaker`` decorator.
    from_state : CircuitState
        The state the circuit was in before the transition.
    to_state : CircuitState
        The state the circuit moved to.
    opened_at : int | None
        Unix timestamp (seconds) the circuit opened, when relevant to the new state.

    Example
    -------
    **Emit a CloudWatch metric per transition**

        from aws_lambda_powertools.metrics import MetricUnit, single_metric

        def emit(transition: CircuitTransition) -> None:
            with single_metric(
                namespace="MyApp",
                name=f"Circuit{transition.to_state}",
                unit=MetricUnit.Count,
                value=1,
            ) as metric:
                metric.add_dimension(name="circuit", value=transition.circuit_name)
    """

    circuit_name: str
    from_state: CircuitState
    to_state: CircuitState
    opened_at: int | None = None
