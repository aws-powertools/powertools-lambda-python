"""
Internal record type for circuit state held in a persistence store.
"""

from __future__ import annotations

from dataclasses import dataclass

from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitInfo, CircuitState


@dataclass
class CircuitStateRecord:
    """
    The persisted state of a single circuit.

    One record exists per circuit name. This is the utility's internal representation;
    user code never sees it directly, only the ``CircuitInfo`` produced by
    :meth:`to_circuit_info`.

    Parameters
    ----------
    name : str
        Circuit name, used as the partition key in the store.
    state : CircuitState
        Current circuit state.
    failure_count : int
        Consecutive failures recorded by the environment that last wrote the record.
    opened_at : int | None
        Unix timestamp (seconds) the circuit opened. Anchors the recovery timeout;
        ``None`` while closed.
    half_open_owner : str | None
        Identifier of the execution environment that won the half-open probe lock, if any.
    expiry_timestamp : int | None
        Unix timestamp (seconds) for the store's TTL attribute.
    """

    name: str
    state: CircuitState
    failure_count: int = 0
    opened_at: int | None = None
    half_open_owner: str | None = None
    expiry_timestamp: int | None = None

    def to_circuit_info(self) -> CircuitInfo:
        """
        Project this record to the public ``CircuitInfo`` handed to user code.

        Strips internal fields (``half_open_owner``, ``expiry_timestamp``) so no
        persistence detail leaks across the public boundary.

        Returns
        -------
        CircuitInfo
            Public snapshot of the circuit.
        """
        return CircuitInfo(
            name=self.name,
            state=self.state,
            failure_count=self.failure_count,
            opened_at=self.opened_at,
        )
