from app import handler


def test_idempotent_lambda_handler(monkeypatch):
    # Set POWERTOOLS_IDEMPOTENCY_DISABLED before calling decorated functions
    monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", 1)

    result = handler()
    ...
