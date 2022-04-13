from src import index


def test_handler(monkeypatch):
    def mockreturn(name):
        return "mock_value"

    monkeypatch.setattr(index.parameters, "get_parameter", mockreturn)
    return_val = index.handler({}, {})
    assert return_val.get("message") == "mock_value"
