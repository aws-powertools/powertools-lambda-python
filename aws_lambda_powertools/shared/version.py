"""
    This file serves to create a constant that informs
    the current version of the Powertools package and exposes it in the main module

    Since Python 3.8 there the built-in importlib.metadata
    When support for Python3.7 is dropped, we can remove the optional importlib_metadata dependency
    See: https://docs.python.org/3/library/importlib.metadata.html
"""
import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import version
else:
    from importlib_metadata import version

VERSION = version("aws-lambda-powertools")
