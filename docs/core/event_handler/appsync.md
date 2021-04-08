---
title: Appsync
description: Core utility
---

Event handler for AWS AppSync Direct Lambda Resolver and Amplify GraphQL Transformer

### Key Features

<!-- * Supports an implicit handler where in `app = AppSyncResolver()` can be invoked directly as `app(event, context)` -->

* Automatically parse API arguments to function arguments
* Choose between strictly match a GraphQL field name or all of them to a function
* Integrates with [Data classes utilities](../../utilities/data_classes.md) to access resolver and identity information

## Terminology

* **[Direct Lambda Resolver](https://docs.aws.amazon.com/appsync/latest/devguide/direct-lambda-reference.html)**. A custom AppSync Resolver to bypass the use of Apache Velocity Template (VTL) and automatically map your function's response to a GraphQL field.
* **[Amplify GraphQL Transformer](https://docs.amplify.aws/cli/graphql-transformer/function)**. Custom GraphQL directives to define your application's data model using Schema Definition Language (SDL). Amplify CLI uses these directives to convert GraphQL SDL into full descriptive AWS CloudFormation templates.

## Getting started

### Required resources

You must have an existing AppSync GraphQL API and IAM permissions to invoke your Lambda function. That said, there is no additional permissions to use this utility.

This is the sample infrastructure we are using for the initial examples with a AppSync Direct Lambda Resolver.

=== "schema.graphql"

    !!! tip "Designing GraphQL Schemas for the first time"
        Visit [AWS AppSync schema documentation](https://docs.aws.amazon.com/appsync/latest/devguide/designing-your-schema.html) for understanding how to define types, nesting, and pagination.

    ```gql
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

AppSync resolver decorator is a concise way to create lambda functions to handle AppSync resolvers for multiple `typeName` and `fieldName` declarations. This decorator builds on top of the [AppSync Resolver ](/utilities/data_classes#appsync-resolver) data class and therefore works with [Amplify GraphQL Transform Library](https://docs.amplify.aws/cli/graphql-transformer/function){target="_blank"} (`@function`),
and [AppSync Direct Lambda Resolvers](https://aws.amazon.com/blogs/mobile/appsync-direct-lambda/){target="_blank"}


## Advanced




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
