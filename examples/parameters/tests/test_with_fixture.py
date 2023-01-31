import pytest
import src.single_mock as single_mock


@pytest.fixture
def mock_parameter_response(monkeypatch):
    def mockreturn(name):
        return "mock_value"

    monkeypatch.setattr(single_mock.parameters, "get_parameter", mockreturn)


# Pass our fixture as an argument to all tests where we want to mock the get_parameter response
def test_handler(mock_parameter_response):
    return_val = single_mock.handler({}, {})
    assert return_val.get("message") == "mock_value"
