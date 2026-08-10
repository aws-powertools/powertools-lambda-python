"""
Abstract persistence layer for the Circuit Breaker utility.

Concrete backends (DynamoDB, cache) subclass :class:`CircuitBreakerPersistenceLayer`
and implement the small set of store primitives. The base class owns the local
read-through cache and the fail-open policy so every backend behaves identically.
"""

from __future__ import annotations

import datetime
import logging
import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple

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


class _CircuitSettings(NamedTuple):
    """Per-circuit tunables the layer captures from :meth:`configure`."""

    local_cache_max_age: int
    recovery_timeout: int


# Fallback for direct layer use before configure() has run; mirrors CircuitBreakerConfig defaults.
_DEFAULT_SETTINGS = _CircuitSettings(local_cache_max_age=5, recovery_timeout=30)


class CircuitBreakerExistingLockError(Exception):
    """Internal signal that a conditional half-open probe write lost the race."""


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
        # Per-circuit tunables, keyed by circuit name. One persistence instance is shared
        # by every circuit (and thread) using the same store, so these must never live in
        # plain instance attributes: circuits with different configs would stamp each
        # other's TTL and probe lease. A plain dict, not an LRUDict: evicting a live
        # circuit's settings would silently swap in the defaults (wrong lease and TTL),
        # whereas evicting a cache entry below only costs a store re-read.
        self._settings: dict[str, _CircuitSettings] = {}
        # Maps circuit name -> the unix timestamp the locally cached record goes stale.
        # Kept separate from the record's durable ``expiry_timestamp`` (the store TTL) so
        # the short in-memory freshness window is never mistaken for the long store TTL.
        self._cache: LRUDict = LRUDict(max_items=LOCAL_CACHE_MAX_ITEMS)
        # One lock for both maps: LRUDict reorders entries even on reads, so unguarded
        # concurrent access can corrupt it or raise.
        self._lock = threading.Lock()

    def configure(self, config: CircuitBreakerConfig, circuit_name: str) -> None:
        """
        Bind a circuit's configuration to the layer.

        Called once per invocation by the handler; the assignment is cheap and the
        same persistence instance is reused across invocations within an environment.

        Parameters
        ----------
        config : CircuitBreakerConfig
            Configuration providing the local cache TTL and recovery timeout.
        circuit_name : str
            The circuit these settings apply to.
        """
        with self._lock:
            self._settings[circuit_name] = _CircuitSettings(
                local_cache_max_age=config.local_cache_max_age,
                recovery_timeout=config.recovery_timeout,
            )

    def _settings_for(self, name: str) -> _CircuitSettings:
        """Return a circuit's configured settings, or the defaults if never configured."""
        with self._lock:
            return self._settings.get(name, _DEFAULT_SETTINGS)

    # ------------------------------------------------------------------ cache

    def _cache_key(self, name: str) -> str:
        return name

    def _durable_ttl(self, name: str) -> int:
        """
        Compute the store TTL stamped on a persisted record.

        Sized to outlive a full recovery window so a live circuit is never reaped
        mid-cycle, while an abandoned circuit (no further writes) self-cleans soon after.
        """
        now = int(datetime.datetime.now().timestamp())
        return now + self._settings_for(name).recovery_timeout + PERSISTED_STATE_TTL_BUFFER

    def _save_to_cache(self, record: CircuitStateRecord) -> None:
        """Cache a record locally with a short in-memory freshness window."""
        local_expiry = int(datetime.datetime.now().timestamp()) + self._settings_for(record.name).local_cache_max_age
        with self._lock:
            self._cache[self._cache_key(record.name)] = (local_expiry, record)

    def _retrieve_from_cache(self, name: str) -> CircuitStateRecord | None:
        """Return a cached record if present and still within its local freshness window."""
        with self._lock:
            cached = self._cache.get(self._cache_key(name))
            if cached is None:
                return None

            local_expiry, record = cached
            if int(datetime.datetime.now().timestamp()) >= local_expiry:
                # Guarded del, not pop: on Python 3.10 OrderedDict.pop re-enters the
                # subclass __getitem__ after detaching the node, so LRUDict.pop raises
                # KeyError for a *present* key and corrupts the dict (fixed in 3.11).
                try:
                    del self._cache[self._cache_key(name)]
                except KeyError:
                    pass
                return None

            return record

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
        except Exception:
            # Fail open without caching, so the next invocation retries the store rather
            # than serving a synthesized CLOSED for the whole local cache window.
            logger.warning(
                "Failed to read circuit state for '%s'; failing open (treating as CLOSED).",
                name,
                exc_info=True,
            )
            return CircuitStateRecord(name=name, state=CircuitState.CLOSED)

        # A missing record is the expected cold-start case, not a failure: treat it as a
        # closed circuit and cache it like any other read.
        if record is None:
            record = CircuitStateRecord(name=name, state=CircuitState.CLOSED)

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
            expiry_timestamp=self._durable_ttl(name),
        )
        self._put_record(record)
        self._save_to_cache(record)

    def try_acquire_half_open(self, name: str, owner: str, opened_at: int) -> bool:
        """
        Atomically elect a single worker to run the half-open probe.

        The conditional write succeeds only when the circuit is OPEN with no existing
        lock owner AND the ``opened_at`` matches what the caller observed (guards against
        stale eventually-consistent reads). A lease expiry is stamped so that if the
        winning worker is recycled before completing the probe, others can take over
        once the lease lapses.

        Parameters
        ----------
        name : str
            Circuit name.
        owner : str
            Identifier of the worker (one thread in one execution environment)
            attempting the probe.
        opened_at : int
            The ``opened_at`` the caller observed, kept stable across the transition.

        Returns
        -------
        bool
            ``True`` if this worker won the probe lock, ``False`` if another
            worker already holds it.
        """
        # Lease = recovery_timeout gives the probe a full cycle to complete.
        probe_lease_expiry = int(datetime.datetime.now().timestamp()) + self._settings_for(name).recovery_timeout
        record = CircuitStateRecord(
            name=name,
            state=CircuitState.HALF_OPEN,
            opened_at=opened_at,
            half_open_owner=owner,
            probe_lease_expiry=probe_lease_expiry,
            expiry_timestamp=self._durable_ttl(name),
        )
        try:
            self._put_record(record, condition="half_open", expected_opened_at=opened_at)
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
            expiry_timestamp=self._durable_ttl(name),
        )
        self._update_record(record)
        self._save_to_cache(record)

    def save_reopen(self, name: str, opened_at: int) -> None:
        """
        Persist a HALF_OPEN to OPEN transition after a failed probe.

        If this write fails the stored row stays in HALF_OPEN, but it does not strand the
        circuit: the probe lease expiry still applies, so once it lapses another
        environment wins the next election and drives the transition.
        """
        record = CircuitStateRecord(
            name=name,
            state=CircuitState.OPEN,
            opened_at=opened_at,
            expiry_timestamp=self._durable_ttl(name),
        )
        self._update_record(record)
        self._save_to_cache(record)

    # --------------------------------------------------------- backend hooks

    @abstractmethod
    def _get_record(self, name: str) -> CircuitStateRecord | None:
        """
        Fetch a circuit record from the store, or ``None`` if no record exists for ``name``.
        """
        raise NotImplementedError

    @abstractmethod
    def _put_record(
        self,
        record: CircuitStateRecord,
        condition: str | None = None,
        expected_opened_at: int | None = None,
    ) -> None:
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
        expected_opened_at : int | None
            When set alongside ``condition="half_open"``, the write additionally
            requires that the stored ``opened_at`` matches this value. This closes
            a race where an eventually-consistent read could let a stale environment
            win an election immediately after a failed probe reopened the circuit.
        """
        raise NotImplementedError

    @abstractmethod
    def _update_record(self, record: CircuitStateRecord) -> None:
        """Update an existing circuit record (unconditional state change)."""
        raise NotImplementedError
