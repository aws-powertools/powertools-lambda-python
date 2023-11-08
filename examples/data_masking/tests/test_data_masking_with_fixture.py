import pytest
from src import single_mock


@pytest.fixture
def mock_data_masking_response(monkeypatch):
    def mockreturn(name):
        return "mock_value"

    monkeypatch.setattr(single_mock.DataMasking, "decrypt", mockreturn)


# Pass our fixture as an argument to all tests where we want to mock the decrypt response
def test_handler(mock_data_masking_response):
    return_val = single_mock.handler({}, {})
    assert return_val.get("message") == "mock_value"
