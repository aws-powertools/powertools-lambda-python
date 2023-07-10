def disable_pydantic_v2_warning():
    """
    Disables the Pydantic version 2 warning by filtering out the related warnings.

    This function checks the version of Pydantic currently installed and if it is version 2,
    it filters out the PydanticDeprecationWarning and PydanticDeprecatedSince20 warnings
    to suppress them.

    Note: This function assumes that Pydantic is already imported.

    Usage:
        disable_pydantic_v2_warning()
    """
    try:
        from pydantic import __version__

        version = __version__.split(".")

        if int(version[0]) == 2:
            import warnings

            from pydantic import PydanticDeprecatedSince20, PydanticDeprecationWarning

            warnings.filterwarnings("ignore", category=PydanticDeprecationWarning)
            warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

    except ImportError:
        pass
