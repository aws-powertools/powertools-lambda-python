import json
from typing import Callable

import pytest

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.middleware_factory.exceptions import MiddlewareInvalidArgumentError


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


def test_factory_exception_propagation(say_bye_middleware, say_hi_middleware):
    @say_bye_middleware
    @say_hi_middleware
    def lambda_handler(evt, ctx):
        raise ValueError("Something happened")

    with pytest.raises(ValueError):
        lambda_handler({}, {})


def test_factory_explicit_tracing(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")

    @lambda_handler_decorator(trace_execution=True)
    def no_op(handler, event, context):
        ret = handler(event, context)
        return ret

    @no_op
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})


def test_factory_explicit_tracing_env_var(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_MIDDLEWARES", "true")
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")

    @lambda_handler_decorator
    def no_op(handler, event, context):
        ret = handler(event, context)
        return ret

    @no_op
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})


def test_factory_decorator_with_kwarg_params(capsys):
    @lambda_handler_decorator
    def log_event(handler, event, context, log_event=False):
        if log_event:
            print(json.dumps(event))
        return handler(event, context)

    @log_event(log_event=True)
    def lambda_handler(evt, ctx):
        return True

    event = {"message": "hello"}
    lambda_handler(event, {})
    output = json.loads(capsys.readouterr().out.strip())

    assert event == output


def test_factory_decorator_with_non_kwarg_params():
    @lambda_handler_decorator
    def log_event(handler, event, context, log_event=False):
        if log_event:
            print(json.dumps(event))
        return handler(event, context)

    with pytest.raises(MiddlewareInvalidArgumentError):

        @log_event(True)
        def lambda_handler(evt, ctx):
            return True


def test_factory_middleware_exception_propagation(say_bye_middleware, say_hi_middleware):
    class CustomMiddlewareException(Exception):
        pass

    @lambda_handler_decorator
    def raise_middleware(handler, evt, ctx):
        raise CustomMiddlewareException("Raise middleware exception")

    @say_bye_middleware
    @raise_middleware
    @say_hi_middleware
    def lambda_handler(evt, ctx):
        return "hello world"

    with pytest.raises(CustomMiddlewareException):
        lambda_handler({}, {})
