from src import single_mock


def test_handler(monkeypatch):
    def mockreturn(name):
        return "mock_value"

    monkeypatch.setattr(single_mock.DataMasking, "decrypt", mockreturn)
    return_val = single_mock.handler({}, {})
    assert return_val.get("message") == "mock_value"
