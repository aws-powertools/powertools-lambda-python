"""Fuzz target for Parser - Pydantic event validation."""

from __future__ import annotations

import sys

import atheris

with atheris.instrument_imports():
    from pydantic import BaseModel, ValidationError

    from aws_lambda_powertools.utilities.parser import parse


class SimpleModel(BaseModel):
    name: str
    value: int


def fuzz_parser(data: bytes) -> None:
    """Fuzz the parser with arbitrary JSON-like data."""
    try:
        parse(event=data.decode("utf-8", errors="ignore"), model=SimpleModel)
    except (ValidationError, ValueError, TypeError, KeyError):
        pass
    except Exception:
        pass


def main() -> None:
    atheris.Setup(sys.argv, fuzz_parser)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
