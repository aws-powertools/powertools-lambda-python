from __future__ import annotations


def construct_build_args(include_extras: bool = True, version: str | None = None) -> str:
    """
    This function creates a suffix string for the Powertools package based on
    whether extra dependencies should be included and a specific version is required.

    Params
    ------
    include_extras: bool | None:
        If True, include all extra dependencies in Powertools package
    version: str | None
        The version of Powertools to install. Can be a version number or a git reference.

    Returns
    -------
    str
        A string suffix to be appended to the Powertools package name during installation.
        Examples:
          - "" (empty string) if no extras or version specified
          - "[all]" if include_extras is True
          - "==1.2.3" if version is "1.2.3"
          - "[all]==1.2.3" if include_extras is True and version is "1.2.3"
          - " @ git+https://github.com/..." if version starts with "git"

    Example
    -------
        >>> construct_build_args(True, "1.2.3")
        '[all]==1.2.3'
        >>> construct_build_args(False, "git+https://github.com/...")
        ' @ git+https://github.com/...'
    """

    suffix = ""

    if include_extras:
        suffix = "[all]"
    if version:
        if version.startswith("git"):
            suffix = f"{suffix} @ {version}"
        else:
            suffix = f"{suffix}=={version}"

    return suffix
