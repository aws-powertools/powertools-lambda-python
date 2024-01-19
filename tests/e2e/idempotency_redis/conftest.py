import pytest


@pytest.fixture(autouse=True, scope="package")
def infrastructure():
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """

    # MAINTENANCE: Add the Stack constructor when Python 3.7 is dropped
    return None
