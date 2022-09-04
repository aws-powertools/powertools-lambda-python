import secrets


def build_service_name() -> str:
    return f"test_service{build_random_value()}"


def build_random_value(nbytes: int = 10) -> str:
    return secrets.token_urlsafe(nbytes).replace("-", "")
