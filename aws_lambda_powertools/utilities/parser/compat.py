import functools


@functools.lru_cache(maxsize=None)
def disable_pydantic_v2_warning():
    """
    Disables the Pydantic version 2 warning by filtering out the related warnings.

    This function checks the version of Pydantic currently installed and if it is version 2,
    it filters out the PydanticDeprecationWarning and PydanticDeprecatedSince20 warnings
    to suppress them.

    Since we only need to run the code once, we are using lru_cache to improve performance.

    Note: This function assumes that Pydantic is installed.

    Usage:
        disable_pydantic_v2_warning()
    """
    try:
        from pydantic import __version__

        version = __version__.split(".")

        if int(version[0]) == 2:  # pragma: no cover  # dropping in v3
            import warnings

            from pydantic import PydanticDeprecatedSince20, PydanticDeprecationWarning

            warnings.filterwarnings("ignore", category=PydanticDeprecationWarning)
            warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

    except ImportError:  # pragma: no cover # false positive; dropping in v3
        pass
