import pytest

from tests.e2e.event_handler_appsync.infrastructure import EventHandlerAppSyncStack


@pytest.fixture(autouse=True, scope="package")
def infrastructure():
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = EventHandlerAppSyncStack()
    try:
        yield stack.deploy()
    finally:
        stack.delete()
