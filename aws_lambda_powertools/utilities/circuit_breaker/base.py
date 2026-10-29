"""
Orchestrator for the Circuit Breaker utility.

:class:`CircuitBreakerHandler` owns the state machine and the per-environment failure
counter; the persistence layer owns the shared truth. This split keeps the healthy
path write-free: failures are counted locally and only persisted on a state transition.
"""

from __future__ import annotations

import datetime as dt
import inspect
import logging
import os
import threading
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.circuit_breaker.exceptions import CircuitBreakerOpenError
from aws_lambda_powertools.utilities.circuit_breaker.states import CircuitState, CircuitTransition

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.circuit_breaker.config import CircuitBreakerConfig
    from aws_lambda_powertools.utilities.circuit_breaker.persistence.base import (
        CircuitBreakerPersistenceLayer,
    )
    from aws_lambda_powertools.utilities.circuit_breaker.persistence.record import CircuitStateRecord
    from aws_lambda_powertools.utilities.circuit_breaker.states import CircuitInfo

logger = logging.getLogger(__name__)

# Per-environment, per-circuit consecutive counters. Module-level so they survive across
# invocations within the same execution environment, the same way idempotency caches do.
_LOCAL_FAILURES: dict[str, int] = {}
_LOCAL_SUCCESSES: dict[str, int] = {}

# Tracks the last state this environment observed from the store, per circuit. Used to
# detect transitions back to CLOSED that happened externally (another env tripped and
# recovered), so stale local failure streaks can be invalidated.
_LAST_OBSERVED_STATE: dict[str, CircuitState] = {}

# Guards the three dicts above. Increments are read-modify-write and a threshold
# crossing must be observed by exactly one thread, so every access goes through this
# lock. Held only while mutating the dicts, never across persistence writes or user
# callbacks.
_COUNTERS_LOCK = threading.Lock()

# Circuit names with a probe currently running in this process. The probe lease is per
# thread, so concurrent coroutines in one event loop would all pass the owner check and
# probe together; this keeps the single-prober guarantee within a process too.
_PROBES_IN_FLIGHT: set[str] = set()

# Identifier used to claim the half-open probe lock, unique per thread so the store's
# conditional election picks a single prober across threads as well as processes.
_PROBE_OWNER = threading.local()


class _Route(Enum):
    """How a call is dispatched after reading the persisted circuit state."""

    CLOSED = "closed"
    PROBE = "probe"
    OPEN = "open"


def _probe_owner_id() -> str:
    """
    Return this thread's stable probe-owner identifier, minting it on first use.

    A uuid in thread-local storage rather than ``threading.get_ident()``: the OS reuses
    thread ids, and a recycled id would let an unrelated thread pass the owner check and
    probe alongside the real owner. The pid check re-mints the id in forked children,
    which inherit the forking thread's local storage.
    """
    pid = os.getpid()
    if getattr(_PROBE_OWNER, "pid", None) != pid:
        _PROBE_OWNER.id = f"{pid}#{uuid.uuid4().hex}"
        _PROBE_OWNER.pid = pid
    return _PROBE_OWNER.id


class CircuitBreakerHandler:
    """
    Drive a single protected call through the circuit breaker state machine.

    A new handler is created per invocation by the decorator. It reads the shared state,
    routes the call (run, short-circuit, or probe), and records the outcome.

    Parameters
    ----------
    function : Callable
        The protected function.
    name : str
        Circuit name.
    config : CircuitBreakerConfig
        Circuit configuration.
    persistence_store : CircuitBreakerPersistenceLayer
        Shared state store.
    on_circuit_open : Callable | None
        Callback invoked with the protected call's own ``*args``/``**kwargs`` plus a
        trailing ``circuit`` keyword argument when the circuit is open. If ``None``, an
        open circuit raises :class:`CircuitBreakerOpenError`.
    function_args : tuple
        Positional arguments the protected function was called with.
    function_kwargs : dict
        Keyword arguments the protected function was called with.
    """

    def __init__(
        self,
        function: Callable,
        name: str,
        config: CircuitBreakerConfig,
        persistence_store: CircuitBreakerPersistenceLayer,
        on_circuit_open: Callable | None = None,
        on_transition: Callable | None = None,
        function_args: tuple | None = None,
        function_kwargs: dict | None = None,
    ):
        self.function = function
        self.name = name
        self.config = config
        self.on_circuit_open = on_circuit_open
        self.on_transition = on_transition
        self.fn_args = function_args or ()
        self.fn_kwargs = function_kwargs or {}

        persistence_store.configure(config=config, circuit_name=name)
        self.persistence_store = persistence_store

    def handle(self) -> Any:
        """
        Evaluate the circuit and route the call.

        Returns
        -------
        Any
            The protected function's result when the call runs, or the
            ``on_circuit_open`` callback's return value when the circuit is open.

        Raises
        ------
        CircuitBreakerOpenError
            If the circuit is open and no callback is registered.
        """
        route, circuit = self._route()
        if route is _Route.CLOSED:
            return self._call_closed()
        if route is _Route.PROBE:
            return self._call_probe()
        return self._open_response(circuit)

    async def handle_async(self) -> Any:
        """Async counterpart of :meth:`handle` for coroutine functions; same routing and bookkeeping."""
        route, circuit = self._route()
        if route is _Route.CLOSED:
            return await self._call_closed_async()
        if route is _Route.PROBE:
            return await self._call_probe_async()
        return await self._open_response_async(circuit)

    def _route(self) -> tuple[_Route, CircuitInfo]:
        """
        Read the persisted state and decide how this call runs.

        Shared by the sync and async paths so the state machine lives in one place. Side
        effects (probe election, OPEN to HALF_OPEN notification) happen here; only the
        protected call itself differs between the two paths.
        """
        record = self.persistence_store.get_state(self.name)

        if record.state == CircuitState.CLOSED:
            # If we previously observed a non-CLOSED state and the circuit is now back to
            # CLOSED, another environment completed the recovery cycle. Reset local counters
            # so a stale partial failure streak doesn't immediately re-trip the circuit.
            with _COUNTERS_LOCK:
                prev = _LAST_OBSERVED_STATE.get(self.name)
                if prev is not None and prev != CircuitState.CLOSED:
                    _LOCAL_FAILURES[self.name] = 0
                _LAST_OBSERVED_STATE[self.name] = CircuitState.CLOSED
            route = _Route.CLOSED
        elif record.state == CircuitState.OPEN:
            route = self._route_open(record)
        else:
            route = self._route_half_open(record)

        return route, record.to_circuit_info()

    def _route_open(self, record: CircuitStateRecord) -> _Route:
        """OPEN: reject, or elect this worker as the single prober once the recovery window elapsed."""
        with _COUNTERS_LOCK:
            _LAST_OBSERVED_STATE[self.name] = CircuitState.OPEN
        # ``opened_at`` may legitimately be 0 (epoch); treat only None as missing.
        opened_at = record.opened_at if record.opened_at is not None else self._now()
        if self._now() < opened_at + self.config.recovery_timeout or not self._claim_probe():
            return _Route.OPEN
        # Recovery window elapsed: try to become the single prober.
        if self.persistence_store.try_acquire_half_open(self.name, _probe_owner_id(), opened_at):
            self._reset_probe_successes()
            self._notify(CircuitState.OPEN, CircuitState.HALF_OPEN, opened_at=opened_at)
            return _Route.PROBE
        self._release_probe()
        return _Route.OPEN

    def _route_half_open(self, record: CircuitStateRecord) -> _Route:
        """HALF_OPEN: only the probe owner runs, one probe at a time; expired leases can be taken over."""
        with _COUNTERS_LOCK:
            _LAST_OBSERVED_STATE[self.name] = CircuitState.HALF_OPEN
        if record.half_open_owner == _probe_owner_id():
            # Owner thread: one probe at a time, even when coroutines run concurrently.
            return _Route.PROBE if self._claim_probe() else _Route.OPEN

        # If the probe lease has expired (owner recycled mid-probe), take over.
        lease_expired = record.probe_lease_expiry is not None and self._now() >= record.probe_lease_expiry
        if lease_expired and self._claim_probe():
            logger.debug("Circuit '%s' probe lease expired; attempting takeover.", self.name)
            if self.persistence_store.try_acquire_half_open(self.name, _probe_owner_id(), record.opened_at or 0):
                self._reset_probe_successes()
                return _Route.PROBE
            self._release_probe()
        return _Route.OPEN

    def _claim_probe(self) -> bool:
        """Mark a probe as in flight for this circuit; False when one is already running in this process."""
        with _COUNTERS_LOCK:
            if self.name in _PROBES_IN_FLIGHT:
                return False
            _PROBES_IN_FLIGHT.add(self.name)
            return True

    def _release_probe(self) -> None:
        with _COUNTERS_LOCK:
            _PROBES_IN_FLIGHT.discard(self.name)

    def _reset_probe_successes(self) -> None:
        """
        Start a fresh probe success streak after this worker wins a probe election.

        ``_LOCAL_SUCCESSES`` lives at module level, so a streak left over from an earlier
        recovery window (this environment probed, then lost the lease, or another
        environment finished that cycle) would otherwise count towards the new one and
        close the circuit after fewer than ``success_threshold`` probes.
        """
        with _COUNTERS_LOCK:
            _LOCAL_SUCCESSES[self.name] = 0

    def _call_closed(self) -> Any:
        """Run the protected call while the circuit is closed, tracking failures."""
        try:
            result = self.function(*self.fn_args, **self.fn_kwargs)
        except Exception as exc:
            self._on_closed_failure(exc)
            raise
        self._on_closed_success()
        return result

    async def _call_closed_async(self) -> Any:
        """Await the protected coroutine while the circuit is closed, tracking failures."""
        try:
            result = await self.function(*self.fn_args, **self.fn_kwargs)
        except Exception as exc:
            self._on_closed_failure(exc)
            raise
        self._on_closed_success()
        return result

    def _on_closed_failure(self, exc: Exception) -> None:
        """Count a qualifying failure while closed and trip the circuit at the threshold."""
        if not self.config.counts_as_failure(exc):
            return
        # Increment and reset atomically so exactly one thread observes the threshold
        # crossing; racing threads would otherwise lose increments (tripping late) or
        # each persist the same transition.
        with _COUNTERS_LOCK:
            failures = _LOCAL_FAILURES.get(self.name, 0) + 1
            tripped = failures >= self.config.failure_threshold
            _LOCAL_FAILURES[self.name] = 0 if tripped else failures
        if tripped:
            logger.debug("Circuit '%s' tripping CLOSED to OPEN after %d failures.", self.name, failures)
            opened_at = self._now()
            self._safe_persist(
                self.persistence_store.save_open,
                self.name,
                failure_count=failures,
                opened_at=opened_at,
            )
            self._notify(CircuitState.CLOSED, CircuitState.OPEN, opened_at=opened_at)

    def _on_closed_success(self) -> None:
        with _COUNTERS_LOCK:
            _LOCAL_FAILURES[self.name] = 0

    def _call_probe(self) -> Any:
        """Run a probe during half-open, closing or reopening based on the outcome."""
        try:
            result = self.function(*self.fn_args, **self.fn_kwargs)
        except Exception as exc:
            self._on_probe_failure(exc)
            raise
        finally:
            self._release_probe()
        self._on_probe_success()
        return result

    async def _call_probe_async(self) -> Any:
        """Await a probe during half-open, closing or reopening based on the outcome."""
        try:
            result = await self.function(*self.fn_args, **self.fn_kwargs)
        except Exception as exc:
            self._on_probe_failure(exc)
            raise
        finally:
            self._release_probe()
        self._on_probe_success()
        return result

    def _on_probe_failure(self, exc: Exception) -> None:
        """A qualifying probe failure reopens the circuit."""
        if not self.config.counts_as_failure(exc):
            return
        logger.debug("Circuit '%s' probe failed; reopening.", self.name)
        opened_at = self._now()
        self._safe_persist(self.persistence_store.save_reopen, self.name, opened_at=opened_at)
        with _COUNTERS_LOCK:
            _LOCAL_SUCCESSES[self.name] = 0
        self._notify(CircuitState.HALF_OPEN, CircuitState.OPEN, opened_at=opened_at)

    def _on_probe_success(self) -> None:
        """Count a probe success and close the circuit at the threshold."""
        with _COUNTERS_LOCK:
            successes = _LOCAL_SUCCESSES.get(self.name, 0) + 1
            closed = successes >= self.config.success_threshold
            _LOCAL_SUCCESSES[self.name] = 0 if closed else successes
            if closed:
                _LOCAL_FAILURES[self.name] = 0
        if closed:
            logger.debug("Circuit '%s' closing after %d probe successes.", self.name, successes)
            self._safe_persist(self.persistence_store.save_closed, self.name)
            self._notify(CircuitState.HALF_OPEN, CircuitState.CLOSED)

    def _safe_persist(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Call a persistence write, swallowing and logging failures.

        State-transition writes must never mask the downstream's real result or replace
        the downstream's real exception. This mirrors the fail-open read policy in the
        persistence layer.
        """
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.warning(
                "Circuit '%s': persistence write (%s) failed; the transition may be delayed but the "
                "downstream result is preserved.",
                self.name,
                getattr(fn, "__name__", repr(fn)),
                exc_info=True,
            )

    def _open_response(self, circuit: CircuitInfo) -> Any:
        """Produce the response for an open circuit: callback result or raise."""
        if self.on_circuit_open is not None:
            # Forward the protected call's arguments unchanged: positional stay positional,
            # keyword stay keyword. The circuit snapshot is passed as a keyword argument so
            # it never collides with positionalized kwargs nor depends on dict ordering.
            return self.on_circuit_open(*self.fn_args, **self.fn_kwargs, circuit=circuit)
        raise CircuitBreakerOpenError(
            f"Circuit '{self.name}' is open.",
            circuit=circuit,
        )

    async def _open_response_async(self, circuit: CircuitInfo) -> Any:
        """Produce the response for an open circuit, awaiting an async ``on_circuit_open`` callback."""
        response = self._open_response(circuit)
        if inspect.isawaitable(response):
            return await response
        return response

    def _notify(self, from_state: CircuitState, to_state: CircuitState, opened_at: int | None = None) -> None:
        """
        Fire the ``on_transition`` hook for a state change.

        Called only on real transitions, never on the hot path. Any exception the hook
        raises is swallowed and logged: observability must never break the protected call.
        """
        if self.on_transition is None:
            return
        try:
            self.on_transition(
                CircuitTransition(
                    circuit_name=self.name,
                    from_state=from_state,
                    to_state=to_state,
                    opened_at=opened_at,
                ),
            )
        except Exception:
            logger.warning("on_transition hook for circuit '%s' raised; ignoring.", self.name, exc_info=True)

    @staticmethod
    def _now() -> int:
        """Current unix timestamp in seconds."""
        return int(dt.datetime.now().timestamp())
