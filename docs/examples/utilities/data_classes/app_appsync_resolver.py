from aws_lambda_powertools.logging import Logger, correlation_paths
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import (
    AppSyncIdentityCognito,
    AppSyncResolverEvent,
)

logger = Logger()


def get_locations(name: str = None, size: int = 0, page: int = 0):
    """Your resolver logic here"""


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def lambda_handler(event, context):
    event: AppSyncResolverEvent = AppSyncResolverEvent(event)

    # Case insensitive look up of request headers
    x_forwarded_for = event.get_header_value("x-forwarded-for")

    # Support for AppSyncIdentityCognito or AppSyncIdentityIAM identity types
    assert isinstance(event.identity, AppSyncIdentityCognito)
    identity: AppSyncIdentityCognito = event.identity

    # Logging with correlation_id
    logger.debug(
        {
            "x-forwarded-for": x_forwarded_for,
            "username": identity.username,
        }
    )

    if event.type_name == "Merchant" and event.field_name == "locations":
        return get_locations(**event.arguments)

    raise ValueError(f"Unsupported field resolver: {event.field_name}")
