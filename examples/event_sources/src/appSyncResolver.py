from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import (
    AppSyncIdentityCognito,
    AppSyncResolverEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=AppSyncResolverEvent)
def lambda_handler(event: AppSyncResolverEvent, context: LambdaContext):
    # Access the AppSync event details
    type_name = event.type_name
    field_name = event.field_name
    arguments = event.arguments
    source = event.source

    print(f"Resolving field '{field_name}' for type '{type_name}'")
    print(f"Arguments: {arguments}")
    print(f"Source: {source}")

    # Check if the identity is Cognito-based
    if isinstance(event.identity, AppSyncIdentityCognito):
        user_id = event.identity.sub
        username = event.identity.username
        print(f"Request from Cognito user: {username} (ID: {user_id})")
    else:
        print("Request is not from a Cognito-authenticated user")

    if type_name == "Merchant" and field_name == "locations":
        page = arguments.get("page", 1)
        size = arguments.get("size", 10)
        name_filter = arguments.get("name")

        # Here you would typically fetch locations from a database
        # This is a mock implementation
        locations = [
            {"id": "1", "name": "Location 1", "address": "123 Main St"},
            {"id": "2", "name": "Location 2", "address": "456 Elm St"},
            {"id": "3", "name": "Location 3", "address": "789 Oak St"},
        ]

        # Apply name filter if provided
        if name_filter:
            locations = [loc for loc in locations if name_filter.lower() in loc["name"].lower()]

        # Apply pagination
        start = (page - 1) * size
        end = start + size
        paginated_locations = locations[start:end]

        return {
            "items": paginated_locations,
            "totalCount": len(locations),
            "nextToken": str(page + 1) if end < len(locations) else None,
        }
    else:
        raise Exception(f"Unhandled field: {field_name} for type: {type_name}")
