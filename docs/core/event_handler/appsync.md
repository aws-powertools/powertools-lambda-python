---
title: GraphQL API
description: Core utility
---

Event handler for AWS AppSync Direct Lambda Resolver and Amplify GraphQL Transformer.

### Key Features

* Automatically parse API arguments to function arguments
* Choose between strictly match a GraphQL field name or all of them to a function
* Integrates with [Data classes utilities](../../utilities/data_classes.md){target="_blank"} to access resolver and identity information
* Works with both Direct Lambda Resolver and Amplify GraphQL Transformer `@function` directive
* Support async Python 3.8+ functions, and generators

## Terminology

**[Direct Lambda Resolver](https://docs.aws.amazon.com/appsync/latest/devguide/direct-lambda-reference.html){target="_blank"}**. A custom AppSync Resolver to bypass the use of Apache Velocity Template (VTL) and automatically map your function's response to a GraphQL field.

**[Amplify GraphQL Transformer](https://docs.amplify.aws/cli/graphql-transformer/function){target="_blank"}**. Custom GraphQL directives to define your application's data model using Schema Definition Language (SDL). Amplify CLI uses these directives to convert GraphQL SDL into full descriptive AWS CloudFormation templates.

## Getting started

### Required resources

You must have an existing AppSync GraphQL API and IAM permissions to invoke your Lambda function. That said, there is no additional permissions to use this utility.

This is the sample infrastructure we are using for the initial examples with a AppSync Direct Lambda Resolver.

???+ tip "Tip: Designing GraphQL Schemas for the first time?"
    Visit [AWS AppSync schema documentation](https://docs.aws.amazon.com/appsync/latest/devguide/designing-your-schema.html){target="_blank"} for understanding how to define types, nesting, and pagination.

=== "schema.graphql"

    ```typescript
    --8<-- "docs/shared/getting_started_schema.graphql"
    ```

=== "template.yml"

    ```yaml hl_lines="37-42 50-55 61-62 78-91 96-120"
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: Hello world Direct Lambda Resolver

    Globals:
      Function:
        Timeout: 5
        Runtime: python3.8
        Tracing: Active
        Environment:
            Variables:
                # Powertools env vars: https://awslabs.github.io/aws-lambda-powertools-python/latest/#environment-variables
                LOG_LEVEL: INFO
                POWERTOOLS_LOGGER_SAMPLE_RATE: 0.1
                POWERTOOLS_LOGGER_LOG_EVENT: true
                POWERTOOLS_SERVICE_NAME: sample_resolver

    Resources:
      HelloWorldFunction:
        Type: AWS::Serverless::Function
        Properties:
            Handler: app.lambda_handler
            CodeUri: hello_world
            Description: Sample Lambda Powertools Direct Lambda Resolver
            Tags:
                SOLUTION: LambdaPowertoolsPython

      # IAM Permissions and Roles

      AppSyncServiceRole:
        Type: "AWS::IAM::Role"
        Properties:
          AssumeRolePolicyDocument:
              Version: "2012-10-17"
              Statement:
                  -
                    Effect: "Allow"
                    Principal:
                        Service:
                            - "appsync.amazonaws.com"
                    Action:
                        - "sts:AssumeRole"

      InvokeLambdaResolverPolicy:
        Type: "AWS::IAM::Policy"
        Properties:
          PolicyName: "DirectAppSyncLambda"
          PolicyDocument:
              Version: "2012-10-17"
              Statement:
                  -
                    Effect: "Allow"
                    Action: "lambda:invokeFunction"
                    Resource:
                        - !GetAtt HelloWorldFunction.Arn
          Roles:
              - !Ref AppSyncServiceRole

      # GraphQL API

      HelloWorldApi:
        Type: "AWS::AppSync::GraphQLApi"
        Properties:
            Name: HelloWorldApi
            AuthenticationType: "API_KEY"
            XrayEnabled: true

      HelloWorldApiKey:
        Type: AWS::AppSync::ApiKey
        Properties:
            ApiId: !GetAtt HelloWorldApi.ApiId

      HelloWorldApiSchema:
        Type: "AWS::AppSync::GraphQLSchema"
        Properties:
            ApiId: !GetAtt HelloWorldApi.ApiId
            Definition: |
                schema {
                    query:Query
                }

                type Query {
                    getTodo(id: ID!): Todo
                    listTodos: [Todo]
                }

                type Todo {
                    id: ID!
                    title: String
                    description: String
                    done: Boolean
                }

      # Lambda Direct Data Source and Resolver

      HelloWorldFunctionDataSource:
        Type: "AWS::AppSync::DataSource"
        Properties:
            ApiId: !GetAtt HelloWorldApi.ApiId
            Name: "HelloWorldLambdaDirectResolver"
            Type: "AWS_LAMBDA"
            ServiceRoleArn: !GetAtt AppSyncServiceRole.Arn
            LambdaConfig:
                LambdaFunctionArn: !GetAtt HelloWorldFunction.Arn

      ListTodosResolver:
        Type: "AWS::AppSync::Resolver"
        Properties:
            ApiId: !GetAtt HelloWorldApi.ApiId
            TypeName: "Query"
            FieldName: "listTodos"
            DataSourceName: !GetAtt HelloWorldFunctionDataSource.Name

      GetTodoResolver:
        Type: "AWS::AppSync::Resolver"
        Properties:
            ApiId: !GetAtt HelloWorldApi.ApiId
            TypeName: "Query"
            FieldName: "getTodo"
            DataSourceName: !GetAtt HelloWorldFunctionDataSource.Name


    Outputs:
      HelloWorldFunction:
        Description: "Hello World Lambda Function ARN"
        Value: !GetAtt HelloWorldFunction.Arn

      HelloWorldAPI:
        Value: !GetAtt HelloWorldApi.Arn
    ```

### Resolver decorator

You can define your functions to match GraphQL types and fields with the `app.resolver()` decorator.

Here's an example where we have two separate functions to resolve `getTodo` and `listTodos` fields within the `Query` type. For completion, we use Scalar type utilities to generate the right output based on our schema definition.

???+ info
    GraphQL arguments are passed as function arguments.

=== "app.py"

    ```python hl_lines="3-5 9 31-32 39-40 47"
    from aws_lambda_powertools import Logger, Tracer

    from aws_lambda_powertools.logging import correlation_paths
    from aws_lambda_powertools.event_handler import AppSyncResolver
    from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils

    tracer = Tracer(service="sample_resolver")
    logger = Logger(service="sample_resolver")
    app = AppSyncResolver()

    # Note that `creation_time` isn't available in the schema
    # This utility also takes into account what info you make available at API level vs what's stored
    TODOS = [
        {
            "id": scalar_types_utils.make_id(), # type ID or String
            "title": "First task",
            "description": "String",
            "done": False,
            "creation_time": scalar_types_utils.aws_datetime(),  # type AWSDateTime
        },
        {
            "id": scalar_types_utils.make_id(),
            "title": "Second task",
            "description": "String",
            "done": True,
            "creation_time": scalar_types_utils.aws_datetime(),
        },
    ]


    @app.resolver(type_name="Query", field_name="getTodo")
    def get_todo(id: str = ""):
        logger.info(f"Fetching Todo {id}")
        todo = [todo for todo in TODOS if todo["id"] == id]

        return todo


    @app.resolver(type_name="Query", field_name="listTodos")
    def list_todos():
        return TODOS


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```

=== "schema.graphql"

    ```typescript
    --8<-- "docs/shared/getting_started_schema.graphql"
    ```

=== "getTodo_event.json"

    ```json
    {
        "arguments": {
          "id": "7e362732-c8cd-4405-b090-144ac9b38960"
        },
        "identity": null,
        "source": null,
        "request": {
          "headers": {
            "x-forwarded-for": "1.2.3.4, 5.6.7.8",
            "accept-encoding": "gzip, deflate, br",
            "cloudfront-viewer-country": "NL",
            "cloudfront-is-tablet-viewer": "false",
            "referer": "https://eu-west-1.console.aws.amazon.com/appsync/home?region=eu-west-1",
            "via": "2.0 9fce949f3749407c8e6a75087e168b47.cloudfront.net (CloudFront)",
            "cloudfront-forwarded-proto": "https",
            "origin": "https://eu-west-1.console.aws.amazon.com",
            "x-api-key": "da1-c33ullkbkze3jg5hf5ddgcs4fq",
            "content-type": "application/json",
            "x-amzn-trace-id": "Root=1-606eb2f2-1babc433453a332c43fb4494",
            "x-amz-cf-id": "SJw16ZOPuMZMINx5Xcxa9pB84oMPSGCzNOfrbJLvd80sPa0waCXzYQ==",
            "content-length": "114",
            "x-amz-user-agent": "AWS-Console-AppSync/",
            "x-forwarded-proto": "https",
            "host": "ldcvmkdnd5az3lm3gnf5ixvcyy.appsync-api.eu-west-1.amazonaws.com",
            "accept-language": "en-US,en;q=0.5",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0",
            "cloudfront-is-desktop-viewer": "true",
            "cloudfront-is-mobile-viewer": "false",
            "accept": "*/*",
            "x-forwarded-port": "443",
            "cloudfront-is-smarttv-viewer": "false"
          }
        },
        "prev": null,
        "info": {
          "parentTypeName": "Query",
          "selectionSetList": [
            "title",
            "id"
          ],
          "selectionSetGraphQL": "{\n  title\n  id\n}",
          "fieldName": "getTodo",
          "variables": {}
        },
        "stash": {}
    }
    ```

=== "listTodos_event.json"

    ```json
    {
        "arguments": {},
        "identity": null,
        "source": null,
        "request": {
          "headers": {
            "x-forwarded-for": "1.2.3.4, 5.6.7.8",
            "accept-encoding": "gzip, deflate, br",
            "cloudfront-viewer-country": "NL",
            "cloudfront-is-tablet-viewer": "false",
            "referer": "https://eu-west-1.console.aws.amazon.com/appsync/home?region=eu-west-1",
            "via": "2.0 9fce949f3749407c8e6a75087e168b47.cloudfront.net (CloudFront)",
            "cloudfront-forwarded-proto": "https",
            "origin": "https://eu-west-1.console.aws.amazon.com",
            "x-api-key": "da1-c33ullkbkze3jg5hf5ddgcs4fq",
            "content-type": "application/json",
            "x-amzn-trace-id": "Root=1-606eb2f2-1babc433453a332c43fb4494",
            "x-amz-cf-id": "SJw16ZOPuMZMINx5Xcxa9pB84oMPSGCzNOfrbJLvd80sPa0waCXzYQ==",
            "content-length": "114",
            "x-amz-user-agent": "AWS-Console-AppSync/",
            "x-forwarded-proto": "https",
            "host": "ldcvmkdnd5az3lm3gnf5ixvcyy.appsync-api.eu-west-1.amazonaws.com",
            "accept-language": "en-US,en;q=0.5",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0",
            "cloudfront-is-desktop-viewer": "true",
            "cloudfront-is-mobile-viewer": "false",
            "accept": "*/*",
            "x-forwarded-port": "443",
            "cloudfront-is-smarttv-viewer": "false"
          }
        },
        "prev": null,
        "info": {
          "parentTypeName": "Query",
          "selectionSetList": [
            "id",
            "title"
          ],
          "selectionSetGraphQL": "{\n  id\n  title\n}",
          "fieldName": "listTodos",
          "variables": {}
        },
        "stash": {}
    }
    ```

## Advanced

### Nested mappings

You can nest `app.resolver()` decorator multiple times when resolving fields with the same return.

=== "nested_mappings.py"

    ```python hl_lines="4 8 10-12 18"
      from aws_lambda_powertools import Logger, Tracer

      from aws_lambda_powertools.logging import correlation_paths
      from aws_lambda_powertools.event_handler import AppSyncResolver

      tracer = Tracer(service="sample_resolver")
      logger = Logger(service="sample_resolver")
      app = AppSyncResolver()

      @app.resolver(field_name="listLocations")
      @app.resolver(field_name="locations")
      def get_locations(name: str, description: str = ""):
          return name + description

      @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
      @tracer.capture_lambda_handler
      def lambda_handler(event, context):
          return app.resolve(event, context)
    ```

=== "schema.graphql"

    ```typescript hl_lines="6 20"
    schema {
        query: Query
    }

    type Query {
        listLocations: [Todo]
    }

    type Location {
        id: ID!
        name: String!
        description: String
        address: String
    }

    type Merchant {
        id: String!
        name: String!
        description: String
        locations: [Location]
    }
    ```

### Async functions

For Lambda Python3.8+ runtime, this utility supports async functions when you use in conjunction with `asyncio.run`.

```python hl_lines="4 8 10-12 20" title="Resolving GraphQL resolvers async"
from aws_lambda_powertools import Logger, Tracer

from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler import AppSyncResolver

tracer = Tracer(service="sample_resolver")
logger = Logger(service="sample_resolver")
app = AppSyncResolver()

@app.resolver(type_name="Query", field_name="listTodos")
async def list_todos():
	todos = await some_async_io_call()
	return todos

@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
	result = app.resolve(event, context)

	return asyncio.run(result)
```

### Amplify GraphQL Transformer

Assuming you have [Amplify CLI installed](https://docs.amplify.aws/cli/start/install){target="_blank"}, create a new API using `amplify add api` and use the following GraphQL Schema.

<!-- AppSync resolver decorator is a concise way to create lambda functions to handle AppSync resolvers for multiple `typeName` and `fieldName` declarations. -->

```typescript hl_lines="7 15 20 22" title="Example GraphQL Schema"
@model
type Merchant {
	id: String!
	name: String!
	description: String
	# Resolves to `common_field`
	commonField: String  @function(name: "merchantInfo-${env}")
}

type Location {
	id: ID!
	name: String!
	address: String
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

[Create two new basic Python functions](https://docs.amplify.aws/cli/function#set-up-a-function){target="_blank"} via `amplify add function`.

???+ note
    Amplify CLI generated functions use `Pipenv` as a dependency manager. Your function source code is located at **`amplify/backend/function/your-function-name`**.

Within your function's folder, add Lambda Powertools as a dependency with `pipenv install aws-lambda-powertools`.

Use the following code for `merchantInfo` and `searchMerchant` functions respectively.

=== "merchantInfo/src/app.py"

    ```python hl_lines="4-5 9 11-12 15-16 23"
    from aws_lambda_powertools import Logger, Tracer

    from aws_lambda_powertools.logging import correlation_paths
    from aws_lambda_powertools.event_handler import AppSyncResolver
    from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils

    tracer = Tracer(service="sample_graphql_transformer_resolver")
    logger = Logger(service="sample_graphql_transformer_resolver")
    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="listLocations")
    def list_locations(page: int = 0, size: int = 10):
        return [{"id": 100, "name": "Smooth Grooves"}]

    @app.resolver(field_name="commonField")
    def common_field():
        # Would match all fieldNames matching 'commonField'
        return scalar_types_utils.make_id()

    @tracer.capture_lambda_handler
    @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
    def lambda_handler(event, context):
        app.resolve(event, context)
    ```
=== "searchMerchant/src/app.py"

    ```python hl_lines="1 4 6-7"
    from aws_lambda_powertools.event_handler import AppSyncResolver
    from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils

    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="findMerchant")
    def find_merchant(search: str):
        return [
          {
            "id": scalar_types_utils.make_id(),
            "name": "Brewer Brewing",
            "description": "Mike Brewer's IPA brewing place"
          },
          {
            "id": scalar_types_utils.make_id(),
            "name": "Serverlessa's Bakery",
            "description": "Lessa's sourdough place"
          },
        ]
    ```

**Example AppSync GraphQL Transformer Function resolver events**

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

### Custom data models

You can subclass `AppSyncResolverEvent` to bring your own set of methods to handle incoming events, by using `data_model` param in the `resolve` method.

=== "custom_model.py"

    ```python hl_lines="11-14 19 26"
      from aws_lambda_powertools import Logger, Tracer

      from aws_lambda_powertools.logging import correlation_paths
      from aws_lambda_powertools.event_handler import AppSyncResolver

      tracer = Tracer(service="sample_resolver")
      logger = Logger(service="sample_resolver")
      app = AppSyncResolver()


      class MyCustomModel(AppSyncResolverEvent):
          @property
          def country_viewer(self) -> str:
              return self.request_headers.get("cloudfront-viewer-country")

      @app.resolver(field_name="listLocations")
      @app.resolver(field_name="locations")
      def get_locations(name: str, description: str = ""):
          if app.current_event.country_viewer == "US":
            ...
          return name + description

      @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
      @tracer.capture_lambda_handler
      def lambda_handler(event, context):
          return app.resolve(event, context, data_model=MyCustomModel)
    ```

=== "schema.graphql"

    ```typescript hl_lines="6 20"
    schema {
        query: Query
    }

    type Query {
        listLocations: [Location]
    }

    type Location {
        id: ID!
        name: String!
        description: String
        address: String
    }

    type Merchant {
        id: String!
        name: String!
        description: String
        locations: [Location]
    }
    ```

=== "listLocations_event.json"

    ```json
    {
      "arguments": {},
      "identity": null,
      "source": null,
      "request": {
        "headers": {
          "x-forwarded-for": "1.2.3.4, 5.6.7.8",
          "accept-encoding": "gzip, deflate, br",
          "cloudfront-viewer-country": "NL",
          "cloudfront-is-tablet-viewer": "false",
          "referer": "https://eu-west-1.console.aws.amazon.com/appsync/home?region=eu-west-1",
          "via": "2.0 9fce949f3749407c8e6a75087e168b47.cloudfront.net (CloudFront)",
          "cloudfront-forwarded-proto": "https",
          "origin": "https://eu-west-1.console.aws.amazon.com",
          "x-api-key": "da1-c33ullkbkze3jg5hf5ddgcs4fq",
          "content-type": "application/json",
          "x-amzn-trace-id": "Root=1-606eb2f2-1babc433453a332c43fb4494",
          "x-amz-cf-id": "SJw16ZOPuMZMINx5Xcxa9pB84oMPSGCzNOfrbJLvd80sPa0waCXzYQ==",
          "content-length": "114",
          "x-amz-user-agent": "AWS-Console-AppSync/",
          "x-forwarded-proto": "https",
          "host": "ldcvmkdnd5az3lm3gnf5ixvcyy.appsync-api.eu-west-1.amazonaws.com",
          "accept-language": "en-US,en;q=0.5",
          "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0",
          "cloudfront-is-desktop-viewer": "true",
          "cloudfront-is-mobile-viewer": "false",
          "accept": "*/*",
          "x-forwarded-port": "443",
          "cloudfront-is-smarttv-viewer": "false"
        }
      },
      "prev": null,
      "info": {
        "parentTypeName": "Query",
        "selectionSetList": [
          "id",
          "name",
          "description"
        ],
        "selectionSetGraphQL": "{\n  id\n  name\n  description\n}",
        "fieldName": "listLocations",
        "variables": {}
      },
      "stash": {}
    }
    ```

### Split operations with Router

???+ tip
    Read the **[considerations section for trade-offs between monolithic and micro functions](./api_gateway.md#considerations){target="_blank"}**, as it's also applicable here.

As you grow the number of related GraphQL operations a given Lambda function should handle, it is natural to split them into separate files to ease maintenance - That's where the `Router` feature is useful.

Let's assume you have `app.py` as your Lambda function entrypoint and routes in `location.py`, this is how you'd use the `Router` feature.

=== "resolvers/location.py"

    We import **Router** instead of **AppSyncResolver**; syntax wise is exactly the same.

	```python hl_lines="4 7 10 15"
    from typing import Any, Dict, List

    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.event_handler.appsync import Router

    logger = Logger(child=True)
    router = Router()


    @router.resolver(type_name="Query", field_name="listLocations")
    def list_locations(merchant_id: str) -> List[Dict[str, Any]]:
        return [{"name": "Location name", "merchant_id": merchant_id}]


    @router.resolver(type_name="Location", field_name="status")
    def resolve_status(merchant_id: str) -> str:
        logger.debug(f"Resolve status for merchant_id: {merchant_id}")
        return "FOO"
	```

=== "app.py"

	We use `include_router` method and include all `location` operations registered in the `router` global object.

    ```python hl_lines="8 13"
    from typing import Dict

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.event_handler import AppSyncResolver
    from aws_lambda_powertools.logging.correlation_paths import APPSYNC_RESOLVER
    from aws_lambda_powertools.utilities.typing import LambdaContext

    from resolvers import location

    tracer = Tracer()
    logger = Logger()
    app = AppSyncResolver()
    app.include_router(location.router)


    @tracer.capture_lambda_handler
    @logger.inject_lambda_context(correlation_id_path=APPSYNC_RESOLVER)
    def lambda_handler(event: Dict, context: LambdaContext):
        app.resolve(event, context)
    ```


## Testing your code

You can test your resolvers by passing a mocked or actual AppSync Lambda event that you're expecting.

You can use either `app.resolve(event, context)` or simply `app(event, context)`.

Here's an example from our internal functional test.

=== "test_direct_resolver.py"

    ```python
    def test_direct_resolver():
      # Check whether we can handle an example appsync direct resolver
      # load_event primarily deserialize the JSON event into a dict
      mock_event = load_event("appSyncDirectResolver.json")

      app = AppSyncResolver()

      @app.resolver(field_name="createSomething")
      def create_something(id: str):
          assert app.lambda_context == {}
          return id

      # Call the implicit handler
      result = app(mock_event, {})

      assert result == "my identifier"
    ```

=== "appSyncDirectResolver.json"

    ```json
    --8<-- "tests/events/appSyncDirectResolver.json"
    ```
