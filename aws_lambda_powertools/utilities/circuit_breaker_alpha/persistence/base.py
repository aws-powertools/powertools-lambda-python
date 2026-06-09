"""
Abstract persistence layer for the Circuit Breaker utility.

Concrete backends (DynamoDB, cache) subclass :class:`CircuitBreakerPersistenceLayer`
and implement the small set of store primitives. The base class owns the local
read-through cache and the fail-open policy so every backend behaves identically.
"""

from __future__ import annotations

import datetime
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from aws_lambda_powertools.shared.cache_dict import LRUDict
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord
from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitState

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.circuit_breaker_alpha.config import CircuitBreakerConfig

logger = logging.getLogger(__name__)

# Circuit names are static in user code, so a handful of circuits per environment is the
# norm. This cap only guards the pathological case of dynamically generated names.
LOCAL_CACHE_MAX_ITEMS = 1024

# Slack added on top of a recovery cycle when computing the durable store TTL. The item
# must outlive any in-flight recovery window so a live circuit is never reaped mid-cycle,
# while an abandoned circuit (no traffic, no further writes) still self-cleans soon after.
PERSISTED_STATE_TTL_BUFFER = 3600


class CircuitBreakerExistingLockError(Exception):
    """Internal signal that a conditional half-open probe write lost the race."""


class CircuitBreakerRecordNotFoundError(Exception):
    """Internal signal that no record exists for a circuit name."""


class CircuitBreakerPersistenceLayer(ABC):
    """
    Abstract base class for circuit breaker persistence layers.

    Owns the per-environment read cache and the fail-open behavior. Subclasses
    implement :meth:`_get_record`, :meth:`_put_record`, and :meth:`_update_record`
    for a specific store.

    A persistence layer is keyed by **circuit name**, not by a payload hash, which is
    the main reason it does not reuse the Idempotency persistence layer.
    """

    def __init__(self) -> None:
        """Initialize defaults; real configuration happens in :meth:`configure`."""
        self.circuit_name: str = ""
        self.local_cache_max_age: int = 5
        self.recovery_timeout: int = 30
        # Maps circuit name -> the unix timestamp the locally cached record goes stale.
        # Kept separate from the record's durable ``expiry_timestamp`` (the store TTL) so
        # the short in-memory freshness window is never mistaken for the long store TTL.
        self._cache: LRUDict = LRUDict(max_items=LOCAL_CACHE_MAX_ITEMS)

    def configure(self, config: CircuitBreakerConfig, circuit_name: str) -> None:
        """
        Bind the layer to a circuit and its configuration.

        Called once per invocation by the handler; the assignments are cheap and the
        same persistence instance is reused across invocations within an environment.

        Parameters
        ----------
        config : CircuitBreakerConfig
            Configuration providing the local cache TTL and recovery timeout.
        circuit_name : str
            The circuit this layer instance serves.
        """
        self.circuit_name = circuit_name
        self.local_cache_max_age = config.local_cache_max_age
        self.recovery_timeout = config.recovery_timeout

    # ------------------------------------------------------------------ cache

    def _cache_key(self, name: str) -> str:
        return name

    def _durable_ttl(self) -> int:
        """
        Compute the store TTL stamped on a persisted record.

        Sized to outlive a full recovery window so a live circuit is never reaped
        mid-cycle, while an abandoned circuit (no further writes) self-cleans soon after.
        """
        return int(datetime.datetime.now().timestamp()) + self.recovery_timeout + PERSISTED_STATE_TTL_BUFFER

    def _save_to_cache(self, record: CircuitStateRecord) -> None:
        """Cache a record locally with a short in-memory freshness window."""
        local_expiry = int(datetime.datetime.now().timestamp()) + self.local_cache_max_age
        self._cache[self._cache_key(record.name)] = (local_expiry, record)

    def _retrieve_from_cache(self, name: str) -> CircuitStateRecord | None:
        """Return a cached record if present and still within its local freshness window."""
        cached = self._cache.get(self._cache_key(name))
        if cached is None:
            return None
        local_expiry, record = cached
        if int(datetime.datetime.now().timestamp()) < local_expiry:
            return record
        del self._cache[self._cache_key(name)]
        return None

    # ------------------------------------------------------------- public API

    def get_state(self, name: str) -> CircuitStateRecord:
        """
        Return the current circuit state, reading the store only on a cache miss.

        A cache miss (cold start or expired local entry) forces a read-through before
        the caller routes the request, so a freshly started environment never assumes a
        circuit is closed without checking.

        Fail-open: if the store read itself raises, the circuit is treated as
        ``CLOSED``. A circuit breaker must never become the outage it is meant to
        prevent.

        Parameters
        ----------
        name : str
            Circuit name.

        Returns
        -------
        CircuitStateRecord
            The current record, a synthesized closed record if none exists yet, or a
            synthesized closed record if the store could not be reached.
        """
        cached = self._retrieve_from_cache(name)
        if cached is not None:
            return cached

        try:
            record = self._get_record(name)
        except CircuitBreakerRecordNotFoundError:
            record = CircuitStateRecord(name=name, state=CircuitState.CLOSED)
        except Exception:
            # Fail open without caching, so the next invocation retries the store rather
            # than serving a synthesized CLOSED for the whole local cache window.
            logger.warning(
                "Failed to read circuit state for '%s'; failing open (treating as CLOSED).",
                name,
                exc_info=True,
            )
            return CircuitStateRecord(name=name, state=CircuitState.CLOSED)

        self._save_to_cache(record)
        return record

    def save_open(self, name: str, failure_count: int, opened_at: int) -> None:
        """
        Persist a CLOSED to OPEN transition.

        Parameters
        ----------
        name : str
            Circuit name.
        failure_count : int
            Consecutive failures that tripped the circuit.
        opened_at : int
            Unix timestamp the circuit opened; anchors the recovery timeout.
        """
        record = CircuitStateRecord(
            name=name,
            state=CircuitState.OPEN,
            failure_count=failure_count,
            opened_at=opened_at,
            expiry_timestamp=self._durable_ttl(),
        )
        self._put_record(record)
        self._save_to_cache(record)

    def try_acquire_half_open(self, name: str, owner: str, opened_at: int) -> bool:
        """
        Atomically elect a single environment to run the half-open probe.

        Parameters
        ----------
        name : str
            Circuit name.
        owner : str
            Identifier of the environment attempting the probe.
        opened_at : int
            The ``opened_at`` the caller observed, kept stable across the transition.

        Returns
        -------
        bool
            ``True`` if this environment won the probe lock, ``False`` if another
            environment already holds it.
        """
        record = CircuitStateRecord(
            name=name,
            state=CircuitState.HALF_OPEN,
            opened_at=opened_at,
            half_open_owner=owner,
            expiry_timestamp=self._durable_ttl(),
        )
        try:
            self._put_record(record, condition="half_open")
        except CircuitBreakerExistingLockError:
            return False
        self._save_to_cache(record)
        return True

    def save_closed(self, name: str) -> None:
        """Persist a transition back to CLOSED and reset counters."""
        record = CircuitStateRecord(
            name=name,
            state=CircuitState.CLOSED,
            failure_count=0,
            expiry_timestamp=self._durable_ttl(),
        )
        self._update_record(record)
        self._save_to_cache(record)

    def save_reopen(self, name: str, opened_at: int) -> None:
        """Persist a HALF_OPEN to OPEN transition after a failed probe."""
        record = CircuitStateRecord(
            name=name,
            state=CircuitState.OPEN,
            opened_at=opened_at,
            expiry_timestamp=self._durable_ttl(),
        )
        self._update_record(record)
        self._save_to_cache(record)

    # --------------------------------------------------------- backend hooks

    @abstractmethod
    def _get_record(self, name: str) -> CircuitStateRecord:
        """
        Fetch a circuit record from the store.

        Raises
        ------
        CircuitBreakerRecordNotFoundError
            If no record exists for ``name``.
        """
        raise NotImplementedError

    @abstractmethod
    def _put_record(self, record: CircuitStateRecord, condition: str | None = None) -> None:
        """
        Write a circuit record.

        Parameters
        ----------
        record : CircuitStateRecord
            Record to write.
        condition : str | None
            When ``"half_open"``, the write must be conditional so only one
            environment wins the probe lock; on a lost race the backend raises
            :class:`CircuitBreakerExistingLockError`.
        """
        raise NotImplementedError

    @abstractmethod
    def _update_record(self, record: CircuitStateRecord) -> None:
        """Update an existing circuit record (unconditional state change)."""
        raise NotImplementedError
