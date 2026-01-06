"""Fuzz target for Validation - JSON Schema validation."""

from __future__ import annotations

import json
import sys

import atheris

with atheris.instrument_imports():
    from aws_lambda_powertools.utilities.validation import validate
    from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError

SIMPLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name"],
}


def fuzz_validation(data: bytes) -> None:
    """Fuzz JSON Schema validation."""
    try:
        event = json.loads(data.decode("utf-8", errors="ignore"))
        validate(event=event, schema=SIMPLE_SCHEMA)
    except (json.JSONDecodeError, SchemaValidationError, TypeError, ValueError):
        pass
    except Exception:
        pass


def main() -> None:
    atheris.Setup(sys.argv, fuzz_validation)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
