import pytest
from src import index


@pytest.fixture
def mock_parameter_response(monkeypatch):
    def mockreturn(name):
        return "mock_value"

    monkeypatch.setattr(index.parameters, "get_parameter", mockreturn)


# Pass our fixture as an argument to all tests where we want to mock the get_parameter response
def test_handler(mock_parameter_response):
    return_val = index.handler({}, {})
    assert return_val.get("message") == "mock_value"
