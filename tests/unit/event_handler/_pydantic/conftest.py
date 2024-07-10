import pytest
from pydantic import __version__


@pytest.fixture(scope="session")
def pydanticv1_only():

    version = __version__.split(".")
    if version[0] != "1":
        pytest.skip("pydanticv1 test only")


@pytest.fixture(scope="session")
def pydanticv2_only():

    version = __version__.split(".")
    if version[0] != "2":
        pytest.skip("pydanticv2 test only")
