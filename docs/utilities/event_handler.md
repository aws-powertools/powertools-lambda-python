---
title: Event Handler
description: Utility
---

Event handler decorators for common Lambda events


### AppSync Resolver Decorator

> New in 1.14.0

=== "schema.graphql"

    ```graphql hl_lines="7-10 17-18 22-25"
    @model
    type Merchant
    {
        id: String!
        name: String!
        description: String
        # Resolves to `get_extra_info`
        extraInfo: ExtraInfo @function(name: "merchantInformation-${env}")
        # Resolves to `common_field`
        commonField: String  @function(name: "merchantInformation-${env}")
    }

    type Location {
        id: ID!
        name: String!
        address: Address
        # Resolves to `common_field`
        commonField: String  @function(name: "merchantInformation-${env}")
    }

    type Query {
      # List of locations resolves to `list_locations`
      listLocations(page: Int, size: Int): [Location] @function(name: "merchantInformation-${env}")
      # List of locations resolves to `list_locations`
      findMerchant(search: str): [Merchant] @function(name: "searchMerchant-${env}")
    }
    ```

Example lambda implementation

=== "merchantInformation app.py"

    ```python hl_lines="1-3 6 8-9 13-14 18-19 23 25"
    from aws_lambda_powertools.logging import Logger, correlation_paths
    from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
    from aws_lambda_powertools.utilities.event_handler import AppSyncResolver

    logger = Logger()
    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="listLocations", include_event=True)
    def list_locations(event: AppSyncResolverEvent, page: int = 0, size: int = 10):
        # Your logic to fetch locations
        ...

    @app.resolver(type_name="Merchant", field_name="extraInfo", include_event=True)
    def get_extra_info(event: AppSyncResolverEvent):
        # Can use `event.source["id"]` to filter within the Merchant context
        ...

    @app.resolver(field_name="commonField")
    def common_field():
        # Would match all fieldNames matching 'commonField'
        ...

    @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
    def handle(event, context):
        app.resolve(event, context)
    ```
=== "searchMerchant app.py"

    ```python hl_lines="1 3 5-6"
    from aws_lambda_powertools.utilities.event_handler import AppSyncResolver

    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="findMerchant")
    def find_merchant(search: str):
        # Your special search function
        ...
    ```

Example AppSync resolver events

=== "Query.listLocations event"

    ```json hl_lines="2-7"
    {
      "typeName": "Query",
      "fieldName": "listLocations",
      "arguments": {
        "page": 2,
        "size": 1
      },
      "identity": {
        "claims": {
          "iat": 1615366261
          ...
        },
        "username": "mike",
        ...
      },
      "request": {
        "headers": {
          "x-amzn-trace-id": "Root=1-60488877-0b0c4e6727ab2a1c545babd0",
          "x-forwarded-for": "127.0.0.1"
          ...
        }
      },
      ...
    }
    ```

=== "Merchant.extraInfo event"

    ```json hl_lines="2 3 14-17"
    {
      "typeName": "Merchant",
      "fieldName": "extraInfo",
      "arguments": {
      },
      "identity": {
        "claims": {
          "iat": 1615366261
          ...
        },
        "username": "mike",
        ...
      },
      "source": {
        "id": "12345",
        "name: "Pizza Parlor"
      },
      "request": {
        "headers": {
          "x-amzn-trace-id": "Root=1-60488877-0b0c4e6727ab2a1c545babd0",
          "x-forwarded-for": "127.0.0.1"
          ...
        }
      },
      ...
    }
    ```

=== "commonField event"

    ```json hl_lines="2 3"
    {
      "typeName": "Merchant",
      "fieldName": "commonField",
      "arguments": {
      },
      "identity": {
        "claims": {
          "iat": 1615366261
          ...
        },
        "username": "mike",
        ...
      },
      "request": {
        "headers": {
          "x-amzn-trace-id": "Root=1-60488877-0b0c4e6727ab2a1c545babd0",
          "x-forwarded-for": "127.0.0.1"
          ...
        }
      },
      ...
    }
    ```

=== "Query.findMerchant event"

    ```json hl_lines="2-6"
    {
      "typeName": "Query",
      "fieldName": "findMerchant",
      "arguments": {
        "search": "Brewers Coffee"
      },
      ...
    }
    ```
