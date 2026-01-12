"""Context propagation helpers for OpenTelemetry tracing."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

    from opentelemetry.trace import Span


def inject_trace_context(carrier: dict[str, Any]) -> dict[str, Any]:
    """Inject current trace context into a carrier dict.

    Use this to propagate trace context through SQS messages.

    Parameters
    ----------
    carrier : dict
        Dictionary to inject trace context into.

    Returns
    -------
    dict
        Carrier with trace context injected.

    Example
    -------
        message = {"data": "payload"}
        message = inject_trace_context(message)
        sqs.send_message(QueueUrl=url, MessageBody=json.dumps(message))
    """
    from opentelemetry.propagate import inject

    inject(carrier)
    return carrier


@contextlib.contextmanager
def create_span_from_context(
    name: str,
    carrier: dict[str, Any],
    **kwargs,
) -> Generator[Span, None, None]:
    """Create a span with parent context extracted from carrier.

    Use this to continue a trace from an SQS message.

    Parameters
    ----------
    name : str
        Span name.
    carrier : dict
        Dictionary containing trace context (e.g., SQS message body).
    **kwargs
        Additional arguments passed to start_as_current_span.

    Example
    -------
        message = json.loads(record["body"])
        with create_span_from_context("process_message", message) as span:
            process(message["data"])
    """
    from opentelemetry import trace
    from opentelemetry.propagate import extract

    ctx = extract(carrier)
    tracer = trace.get_tracer("aws_lambda_powertools")

    kwargs.setdefault("record_exception", True)
    kwargs.setdefault("set_status_on_exception", True)

    with tracer.start_as_current_span(name=name, context=ctx, **kwargs) as span:
        yield span
