try:
    from pydantic.version import VERSION as PYDANTIC_VERSION

    PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")
except ImportError:
    PYDANTIC_V2 = False  # pragma: no cover  # false positive; dropping in v3
