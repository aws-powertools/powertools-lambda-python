from typing import Dict

from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.logging.logger import Logger
from aws_lambda_powertools.utilities.data_classes.appsync_authorizer_event import (
    AppSyncAuthorizerEvent,
    AppSyncAuthorizerResponse,
)
from aws_lambda_powertools.utilities.data_classes.event_source import event_source

logger = Logger()


def get_user_by_token(token: str):
    """Look a user by token"""
    ...


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_AUTHORIZER)
@event_source(data_class=AppSyncAuthorizerEvent)
def lambda_handler(event: AppSyncAuthorizerEvent, context) -> Dict:
    user = get_user_by_token(event.authorization_token)

    if not user:
        # No user found, return not authorized
        return AppSyncAuthorizerResponse().asdict()

    return AppSyncAuthorizerResponse(
        authorize=True,
        resolver_context={"id": user.id},
        # Only allow admins to delete events
        deny_fields=None if user.is_admin else ["Mutation.deleteEvent"],
    ).asdict()
