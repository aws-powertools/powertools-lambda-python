---
title: Event Source Data Classes
description: Utility
---

Event Source Data Classes utility provides classes self-describing Lambda event sources.

## Key Features

* Type hinting and code completion for common event types
* Helper functions for decoding/deserializing nested fields
* Docstrings for fields contained in event schemas

**Background**

When authoring Lambda functions, you often need to understand the schema of the event dictionary which is passed to the
handler. There are several common event types which follow a specific schema, depending on the service triggering the
Lambda function.

## Getting started

### Utilizing the data classes

The classes are initialized by passing in the Lambda event object into the constructor of the appropriate data class or
by using the `event_source` decorator.

For example, if your Lambda function is being triggered by an API Gateway proxy integration, you can use the
`APIGatewayProxyEvent` class.

=== "app.py"

    ```python hl_lines="1 5"
    --8<-- "docs/examples/utilities/data_classes/using_data_classes.py"
    ```

Same example as above, but using the `event_source` decorator

=== "app.py"

    ```python hl_lines="1 4"
    --8<-- "docs/examples/utilities/data_classes/using_data_classes_event_source.py"
    ```

**Autocomplete with self-documented properties and methods**

![Utilities Data Classes](../media/utilities_data_classes.png)

## Supported event sources

Event Source | Data_class
------------------------------------------------- | ---------------------------------------------------------------------------------
[Active MQ](#active-mq) | `ActiveMQEvent`
[API Gateway Authorizer](#api-gateway-authorizer) | `APIGatewayAuthorizerRequestEvent`
[API Gateway Authorizer V2](#api-gateway-authorizer-v2) | `APIGatewayAuthorizerEventV2`
[API Gateway Proxy](#api-gateway-proxy) | `APIGatewayProxyEvent`
[API Gateway Proxy V2](#api-gateway-proxy-v2) | `APIGatewayProxyEventV2`
[Application Load Balancer](#application-load-balancer) | `ALBEvent`
[AppSync Authorizer](#appsync-authorizer) | `AppSyncAuthorizerEvent`
[AppSync Resolver](#appsync-resolver) | `AppSyncResolverEvent`
[CloudWatch Logs](#cloudwatch-logs) | `CloudWatchLogsEvent`
[CodePipeline Job Event](#codepipeline-job) | `CodePipelineJobEvent`
[Cognito User Pool](#cognito-user-pool) | Multiple available under `cognito_user_pool_event`
[Connect Contact Flow](#connect-contact-flow) | `ConnectContactFlowEvent`
[DynamoDB streams](#dynamodb-streams) | `DynamoDBStreamEvent`, `DynamoDBRecordEventName`
[EventBridge](#eventbridge) | `EventBridgeEvent`
[Kinesis Data Stream](#kinesis-streams) | `KinesisStreamEvent`
[Rabbit MQ](#rabbit-mq) | `RabbitMQEvent`
[S3](#s3) | `S3Event`
[S3 Object Lambda](#s3-object-lambda) | `S3ObjectLambdaEvent`
[SES](#ses) | `SESEvent`
[SNS](#sns) | `SNSEvent`
[SQS](#sqs) | `SQSEvent`

???+ info
    The examples provided below are far from exhaustive - the data classes themselves are designed to provide a form of
    documentation inherently (via autocompletion, types and docstrings).

### Active MQ

It is used for [Active MQ payloads](https://docs.aws.amazon.com/lambda/latest/dg/with-mq.html){target="_blank"}, also see
the [AWS blog post](https://aws.amazon.com/blogs/compute/using-amazon-mq-as-an-event-source-for-aws-lambda/){target="_blank"}
for more details.

=== "app.py"

    ```python hl_lines="4-5 10-11"
    --8<-- "docs/examples/utilities/data_classes/app_active_mq.py"
    ```

### API Gateway Authorizer

> New in 1.20.0

It is used for [API Gateway Rest API Lambda Authorizer payload](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html){target="_blank"}.

Use **`APIGatewayAuthorizerRequestEvent`** for type `REQUEST` and **`APIGatewayAuthorizerTokenEvent`** for type `TOKEN`.

=== "app_type_request.py"

    This example uses the `APIGatewayAuthorizerResponse` to decline a given request if the user is not found.

    When the user is found, it includes the user details in the request context that will be available to the back-end, and returns a full access policy for admin users.

    ```python hl_lines="4-9 30 37-44 48 50 52"
    --8<-- "docs/examples/utilities/data_classes/app_rest_api_type_request.py"
    ```
=== "app_type_token.py"

    ```python hl_lines="2-5 12-18 21 23-24"
    --8<-- "docs/examples/utilities/data_classes/app_rest_api_type_token.py"
    ```

### API Gateway Authorizer V2

> New in 1.20.0

It is used for [API Gateway HTTP API Lambda Authorizer payload version 2](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html){target="_blank"}.
See also [this blog post](https://aws.amazon.com/blogs/compute/introducing-iam-and-lambda-authorizers-for-amazon-api-gateway-http-apis/){target="_blank"} for more details.

=== "app.py"

    This example looks up user details via `x-token` header. It uses `APIGatewayAuthorizerResponseV2` to return a deny policy when user is not found or authorized.

    ```python hl_lines="4-7 21 24"
    --8<-- "docs/examples/utilities/data_classes/app_http_api_authorizer.py"
    ```

### API Gateway Proxy

It is used for either API Gateway REST API or HTTP API using v1 proxy event.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_rest_api.py"
    ```

### API Gateway Proxy V2

It is used for HTTP API using v2 proxy event.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_http_api.py"
    ```

### Application Load Balancer

Is it used for Application load balancer event.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_alb.py"
    ```

### AppSync Authorizer

> New in 1.20.0

Used when building an [AWS_LAMBDA Authorization](https://docs.aws.amazon.com/appsync/latest/devguide/security-authz.html#aws-lambda-authorization){target="_blank"} with AppSync.
See blog post [Introducing Lambda authorization for AWS AppSync GraphQL APIs](https://aws.amazon.com/blogs/mobile/appsync-lambda-auth/){target="_blank"}
or read the Amplify documentation on using [AWS Lambda for authorization](https://docs.amplify.aws/lib/graphqlapi/authz/q/platform/js#aws-lambda){target="_blank"} with AppSync.

In this example extract the `requestId` as the `correlation_id` for logging, used `@event_source` decorator and builds the AppSync authorizer using the `AppSyncAuthorizerResponse` helper.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_appsync_authorizer.py"
    ```

### AppSync Resolver

> New in 1.12.0

Used when building Lambda GraphQL Resolvers with [Amplify GraphQL Transform Library](https://docs.amplify.aws/cli/graphql-transformer/function){target="_blank"} (`@function`),
and [AppSync Direct Lambda Resolvers](https://aws.amazon.com/blogs/mobile/appsync-direct-lambda/){target="_blank"}.

In this example, we also use the new Logger `correlation_id` and built-in `correlation_paths` to extract, if available, X-Ray Trace ID in AppSync request headers:

=== "app.py"

    ```python hl_lines="2-5 14 16 21 23 33-34"
    --8<-- "docs/examples/utilities/data_classes/app_appsync_resolver.py"
    ```

=== "Example AppSync Event"

    ```json hl_lines="2-8 14 19 20"
    {
      "typeName": "Merchant",
      "fieldName": "locations",
      "arguments": {
        "page": 2,
        "size": 1,
        "name": "value"
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

=== "Example CloudWatch Log"

    ```json hl_lines="5 6 16"
    {
        "level":"DEBUG",
        "location":"lambda_handler:22",
        "message":{
            "x-forwarded-for":"127.0.0.1",
            "username":"mike"
        },
        "timestamp":"2021-03-10 12:38:40,062",
        "service":"service_undefined",
        "sampling_rate":0.0,
        "cold_start":true,
        "function_name":"func_name",
        "function_memory_size":512,
        "function_arn":"func_arn",
        "function_request_id":"6735a29c-c000-4ae3-94e6-1f1c934f7f94",
        "correlation_id":"Root=1-60488877-0b0c4e6727ab2a1c545babd0"
    }
    ```

### CloudWatch Logs

CloudWatch Logs events by default are compressed and base64 encoded. You can use the helper function provided to decode,
decompress and parse json data from the event.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_cloudwatch_logs.py"
    ```

### CodePipeline Job

Data classes and utility functions to help create continuous delivery pipelines tasks with AWS Lambda

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_codepipeline_job.py"
    ```

### Cognito User Pool

Cognito User Pools have several [different Lambda trigger sources](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools-working-with-aws-lambda-triggers.html#cognito-user-identity-pools-working-with-aws-lambda-trigger-sources), all of which map to a different data class, which
can be imported from `aws_lambda_powertools.data_classes.cognito_user_pool_event`:

Trigger/Event Source | Data Class
------------------------------------------------- | -------------------------------------------------
Custom message event | `data_classes.cognito_user_pool_event.CustomMessageTriggerEvent`
Post authentication | `data_classes.cognito_user_pool_event.PostAuthenticationTriggerEvent`
Post confirmation | `data_classes.cognito_user_pool_event.PostConfirmationTriggerEvent`
Pre authentication | `data_classes.cognito_user_pool_event.PreAuthenticationTriggerEvent`
Pre sign-up | `data_classes.cognito_user_pool_event.PreSignUpTriggerEvent`
Pre token generation | `data_classes.cognito_user_pool_event.PreTokenGenerationTriggerEvent`
User migration | `data_classes.cognito_user_pool_event.UserMigrationTriggerEvent`
Define Auth Challenge | `data_classes.cognito_user_pool_event.DefineAuthChallengeTriggerEvent`
Create Auth Challenge | `data_classes.cognito_user_pool_event.CreateAuthChallengeTriggerEvent`
Verify Auth Challenge | `data_classes.cognito_user_pool_event.VerifyAuthChallengeResponseTriggerEvent`

#### Post Confirmation Example

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_cognito_post_confirmation.py"
    ```

#### Define Auth Challenge Example

???+ note
    In this example we are modifying the wrapped dict response fields, so we need to return the json serializable wrapped event in `event.raw_event`.

This example is based on the AWS Cognito docs for [Define Auth Challenge Lambda Trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-define-auth-challenge.html){target="_blank"}.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_cognito_define_auth_challenge.py"
    ```
=== "SPR_A response"

    ```json hl_lines="25-27"
    {
        "version": "1",
        "region": "us-east-1",
        "userPoolId": "us-east-1_example",
        "userName": "UserName",
        "callerContext": {
            "awsSdkVersion": "awsSdkVersion",
            "clientId": "clientId"
        },
        "triggerSource": "DefineAuthChallenge_Authentication",
        "request": {
            "userAttributes": {
                "sub": "4A709A36-7D63-4785-829D-4198EF10EBDA",
                "email_verified": "true",
                "name": "First Last",
                "email": "define-auth@mail.com"
            },
            "session": [
                {
                    "challengeName": "SRP_A",
                    "challengeResult": true
                }
            ]
        },
        "response": {
            "issueTokens": false,
            "failAuthentication": false,
            "challengeName": "PASSWORD_VERIFIER"
        }
    }
    ```
=== "PASSWORD_VERIFIER success response"

    ```json hl_lines="30-32"
    {
        "version": "1",
        "region": "us-east-1",
        "userPoolId": "us-east-1_example",
        "userName": "UserName",
        "callerContext": {
            "awsSdkVersion": "awsSdkVersion",
            "clientId": "clientId"
        },
        "triggerSource": "DefineAuthChallenge_Authentication",
        "request": {
            "userAttributes": {
                "sub": "4A709A36-7D63-4785-829D-4198EF10EBDA",
                "email_verified": "true",
                "name": "First Last",
                "email": "define-auth@mail.com"
            },
            "session": [
                {
                    "challengeName": "SRP_A",
                    "challengeResult": true
                },
                {
                    "challengeName": "PASSWORD_VERIFIER",
                    "challengeResult": true
                }
            ]
        },
        "response": {
            "issueTokens": false,
            "failAuthentication": false,
            "challengeName": "CUSTOM_CHALLENGE"
        }
    }

    ```
=== "CUSTOM_CHALLENGE success response"

    ```json hl_lines="34 35"
    {
        "version": "1",
        "region": "us-east-1",
        "userPoolId": "us-east-1_example",
        "userName": "UserName",
        "callerContext": {
            "awsSdkVersion": "awsSdkVersion",
            "clientId": "clientId"
        },
        "triggerSource": "DefineAuthChallenge_Authentication",
        "request": {
            "userAttributes": {
                "sub": "4A709A36-7D63-4785-829D-4198EF10EBDA",
                "email_verified": "true",
                "name": "First Last",
                "email": "define-auth@mail.com"
            },
            "session": [
                {
                    "challengeName": "SRP_A",
                    "challengeResult": true
                },
                {
                    "challengeName": "PASSWORD_VERIFIER",
                    "challengeResult": true
                },
                {
                    "challengeName": "CUSTOM_CHALLENGE",
                    "challengeResult": true
                }
            ]
        },
        "response": {
            "issueTokens": true,
            "failAuthentication": false
        }
    }
    ```

#### Create Auth Challenge Example

This example is based on the AWS Cognito docs for [Create Auth Challenge Lambda Trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-create-auth-challenge.html){target="_blank"}.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_cognito_create_auth_challenge.py"
    ```

#### Verify Auth Challenge Response Example

This example is based on the AWS Cognito docs for [Verify Auth Challenge Response Lambda Trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-verify-auth-challenge-response.html){target="_blank"}.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_cognito_verify_auth_challenge_response.py"
    ```

### Connect Contact Flow

> New in 1.11.0

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_connect_contact_flow.py"
    ```

### DynamoDB Streams

The DynamoDB data class utility provides the base class for `DynamoDBStreamEvent`, a typed class for
attributes values (`AttributeValue`), as well as enums for stream view type (`StreamViewType`) and event type
(`DynamoDBRecordEventName`).

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_dynamodb.py"
    ```

=== "multiple_records_types.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_dynamodb_multiple_records_types.py"
    ```

### EventBridge

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_event_bridge.py"
    ```

### Kinesis streams

Kinesis events by default contain base64 encoded data. You can use the helper function to access the data either as json
or plain text, depending on the original payload.

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_kinesis_data_streams.py"
    ```

### Rabbit MQ

It is used for [Rabbit MQ payloads](https://docs.aws.amazon.com/lambda/latest/dg/with-mq.html){target="_blank"}, also see
the [blog post](https://aws.amazon.com/blogs/compute/using-amazon-mq-for-rabbitmq-as-an-event-source-for-lambda/){target="_blank"}
for more details.

=== "app.py"

    ```python hl_lines="4-5 10-11"
    --8<-- "docs/examples/utilities/data_classes/app_rabbit_mq.py"
    ```

### S3

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_s3.py"
    ```

### S3 Object Lambda

This example is based on the AWS Blog post [Introducing Amazon S3 Object Lambda – Use Your Code to Process Data as It Is Being Retrieved from S3](https://aws.amazon.com/blogs/aws/introducing-amazon-s3-object-lambda-use-your-code-to-process-data-as-it-is-being-retrieved-from-s3/){target="_blank"}.

=== "app.py"

    ```python hl_lines="5-6 13 15"
    --8<-- "docs/examples/utilities/data_classes/app_s3_object_lambda.py"
    ```

### SES

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_ses.py"
    ```

### SNS

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_sns.py"
    ```

### SQS

=== "app.py"

    ```python
    --8<-- "docs/examples/utilities/data_classes/app_sqs.py"
    ```
