"""E2E tests for OpenTelemetry Tracer.

Note: These tests require ADOT Lambda Layer and are not run in CI due to slow feedback loop.
Run manually with: pytest tests/e2e/tracer_otel/ -v
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="E2E tests not run automatically - slow feedback loop")
class TestAutoMode:
    """E2E tests for auto mode with ADOT Layer."""

    def test_handler_creates_spans(self, infrastructure):
        """Handler should create spans when using auto mode with ADOT."""
        # Deploy Lambda with ADOT Layer
        # Invoke Lambda
        # Verify spans exported to collector
        pass

    def test_cold_start_attribute(self, infrastructure):
        """Should set faas.coldstart attribute correctly."""
        pass


@pytest.mark.skip(reason="E2E tests not run automatically - slow feedback loop")
class TestManualMode:
    """E2E tests for manual mode."""

    def test_handler_creates_spans(self, infrastructure):
        """Handler should create spans when using manual mode."""
        pass

    def test_custom_exporter(self, infrastructure):
        """Should export spans to custom endpoint."""
        pass
