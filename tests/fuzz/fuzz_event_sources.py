"""Fuzz target for Event Source Data Classes - SQS, SNS, API Gateway, Kinesis parsing."""

from __future__ import annotations

import json
import sys

import atheris

with atheris.instrument_imports():
    from aws_lambda_powertools.utilities.data_classes import (
        APIGatewayProxyEvent,
        KinesisStreamEvent,
        SNSEvent,
        SQSEvent,
    )


def fuzz_sqs_event(data: bytes) -> None:
    """Fuzz SQS event parsing."""
    try:
        event_dict = json.loads(data.decode("utf-8", errors="ignore"))
        SQSEvent(event_dict)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    except Exception:
        pass


def fuzz_sns_event(data: bytes) -> None:
    """Fuzz SNS event parsing."""
    try:
        event_dict = json.loads(data.decode("utf-8", errors="ignore"))
        SNSEvent(event_dict)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    except Exception:
        pass


def fuzz_api_gateway_event(data: bytes) -> None:
    """Fuzz API Gateway event parsing."""
    try:
        event_dict = json.loads(data.decode("utf-8", errors="ignore"))
        APIGatewayProxyEvent(event_dict)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    except Exception:
        pass


def fuzz_kinesis_event(data: bytes) -> None:
    """Fuzz Kinesis event parsing."""
    try:
        event_dict = json.loads(data.decode("utf-8", errors="ignore"))
        KinesisStreamEvent(event_dict)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    except Exception:
        pass


def fuzz_all_events(data: bytes) -> None:
    """Fuzz all event sources."""
    fuzz_sqs_event(data)
    fuzz_sns_event(data)
    fuzz_api_gateway_event(data)
    fuzz_kinesis_event(data)


def main() -> None:
    atheris.Setup(sys.argv, fuzz_all_events)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
