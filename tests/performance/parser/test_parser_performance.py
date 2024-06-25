import time
from contextlib import contextmanager
from typing import Annotated, Generator, Literal, Union

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser import parse

# adjusted for slower machines in CI too
PARSER_VALIDATION_SLA: float = 0.002


@contextmanager
def timing() -> Generator:
    """ "Generator to quickly time operations. It can add 5ms so take that into account in elapsed time

    Examples
    --------

        with timing() as t:
            print("something")
        elapsed = t()
    """
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start  # gen as lambda to calculate elapsed time


class SuccessfulCallback(BaseModel):
    status: Literal["succeeded"]
    name: str
    breed: Literal["Husky", "Labrador"]


class FailedCallback(BaseModel):
    status: Literal["failed"]
    error: str


class TemporaryErrorCallback(BaseModel):
    status: Literal["temporary_error"]
    error: str


class PartisalSuccessCallback(BaseModel):
    status: Literal["partial_success"]
    name: str
    breed: Literal["Husky", "Labrador"]


DogCallback = Annotated[
    Union[SuccessfulCallback, FailedCallback, PartisalSuccessCallback, TemporaryErrorCallback],
    Field(discriminator="status"),
]


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_parser_with_cache():
    event = {"status": "temporary_error", "error": "X"}

    # WHEN we call parser 999 times
    with timing() as t:
        for _ in range(999):
            parse(event=event, model=DogCallback)

    # THEN completion time should be below our validation SLA
    elapsed = t()
    if elapsed > PARSER_VALIDATION_SLA:
        pytest.fail(f"Parser validation should be below {PARSER_VALIDATION_SLA}s: {elapsed}")
