---
title: Appsync
description: Core utility
---

Event handler decorators for common Lambda events


## AppSync Resolver Decorator

> New in 1.14.0

AppSync resolver decorator is a concise way to create lambda functions to handle AppSync resolvers for multiple
`typeName` and `fieldName` declarations. This decorator builds on top of the
[AppSync Resolver ](/utilities/data_classes#appsync-resolver) data class and therefore works with [Amplify GraphQL Transform Library](https://docs.amplify.aws/cli/graphql-transformer/function){target="_blank"} (`@function`),
and [AppSync Direct Lambda Resolvers](https://aws.amazon.com/blogs/mobile/appsync-direct-lambda/){target="_blank"}

### Key Features

* Works with any of the existing Powertools utilities by allow you to create your own `lambda_handler` function
* Supports an implicit handler where in `app = AppSyncResolver()` can be invoked directly as `app(event, context)`
* `resolver` decorator has flexible or strict matching against `fieldName`
* Arguments are automatically passed into your function
* AppSyncResolver includes `current_event` and `lambda_cotext` fields can be used to pass in the original `AppSyncResolver` or `LambdaContext`
 objects

###  Amplify GraphQL Example

Create a new GraphQL api via `amplify add api` and add the following to the new `schema.graphql`

=== "schema.graphql"

    ```typescript hl_lines="7-10 17-18 22-25"
    @model
    type Merchant
    {
        id: String!
        name: String!
        description: String
        # Resolves to `get_extra_info`
        extraInfo: ExtraInfo @function(name: "merchantInfo-${env}")
        # Resolves to `common_field`
        commonField: String  @function(name: "merchantInfo-${env}")
    }

    type Location {
        id: ID!
        name: String!
        address: Address
        # Resolves to `common_field`
        commonField: String  @function(name: "merchantInfo-${env}")
    }

    type Query {
      # List of locations resolves to `list_locations`
      listLocations(page: Int, size: Int): [Location] @function(name: "merchantInfo-${env}")
      # List of locations resolves to `list_locations`
      findMerchant(search: str): [Merchant] @function(name: "searchMerchant-${env}")
    }
    ```

Create two new simple Python functions via `amplify add function` and run `pipenv install aws-lambda-powertools` to
add Powertools as a dependency. Add the following example lambda implementation

=== "merchantInfo/src/app.py"

    ```python hl_lines="1-2 6 8-9 13-14 18-19 24 26"
    from aws_lambda_powertools.event_handler import AppSyncResolver
    from aws_lambda_powertools.logging import Logger, Tracer, correlation_paths

    tracer = Tracer()
    logger = Logger()
    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="listLocations")
    def list_locations(page: int = 0, size: int = 10):
        # Your logic to fetch locations
        ...

    @app.resolver(type_name="Merchant", field_name="extraInfo")
    def get_extra_info():
        # Can use `app.current_event.source["id"]` to filter within the Merchant context
        ...

    @app.resolver(field_name="commonField")
    def common_field():
        # Would match all fieldNames matching 'commonField'
        ...

    @tracer.capture_lambda_handler
    @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
    def lambda_handler(event, context):
        app.resolve(event, context)
    ```
=== "searchMerchant/src/app.py"

    ```python hl_lines="1 3 5-6"
    from aws_lambda_powertools.event_handler import AppSyncResolver

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

    ```json hl_lines="2-5 14-17"
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

=== "*.commonField event"

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
