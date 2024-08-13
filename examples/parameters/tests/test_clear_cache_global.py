from __future__ import annotations

import pytest
from src import app

from aws_lambda_powertools.utilities import parameters


@pytest.fixture(scope="function", autouse=True)
def clear_parameters_cache():
    yield
    parameters.clear_caches()  # This will clear all providers cache


@pytest.fixture
def mock_parameter_response(monkeypatch):
    def mockreturn(name):
        return "mock_value"

    monkeypatch.setattr(app.ssm_provider, "get", mockreturn)


# Pass our fixture as an argument to all tests where we want to mock the get_parameter response
def test_handler(mock_parameter_response):
    return_val = app.handler({}, {})
    assert return_val.get("message") == "mock_value"
