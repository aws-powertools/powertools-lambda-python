import json
from typing import Callable

import pytest

from aws_lambda_powertools.utils.factory import lambda_handler_decorator


@pytest.fixture
def say_hi_middleware() -> Callable:
    @lambda_handler_decorator
    def say_hi(handler, event, context):
        print("hi before lambda handler is executed")
        return handler(event, context)

    return say_hi


@pytest.fixture
def say_bye_middleware() -> Callable:
    @lambda_handler_decorator
    def say_bye(handler, event, context):
        ret = handler(event, context)
        print("goodbye after lambda handler is executed")
        return ret

    return say_bye


def test_factory_single_decorator(capsys, say_hi_middleware):
    @say_hi_middleware
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})
    output = capsys.readouterr().out.strip()
    assert "hi before lambda handler is executed" in output


def test_factory_nested_decorator(capsys, say_hi_middleware, say_bye_middleware):
    @say_bye_middleware
    @say_hi_middleware
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})
    output = capsys.readouterr().out.strip()
    assert "hi before lambda handler is executed" in output
    assert "goodbye after lambda handler is executed" in output


def test_factory_exception_propagation(capsys, say_bye_middleware, say_hi_middleware):
    @say_bye_middleware
    @say_hi_middleware
    def lambda_handler(evt, ctx):
        raise ValueError("Something happened")

    with pytest.raises(ValueError):
        lambda_handler({}, {})
