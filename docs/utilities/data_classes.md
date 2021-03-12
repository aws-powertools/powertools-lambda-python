---
title: Event Source Data Classes
description: Utility
---

The event source data classes utility provides classes describing the schema of common Lambda events triggers.

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

The classes are initialized by passing in the Lambda event object into the constructor of the appropriate data class.

For example, if your Lambda function is being triggered by an API Gateway proxy integration, you can use the
`APIGatewayProxyEvent` class.

=== "app.py"

    ```python hl_lines="1 4"
    from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

    def lambda_handler(event, context):
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)

        if 'helloworld' in event.path and event.http_method == 'GET':
            do_something_with(event.body, user)
    ```

**Autocomplete with self-documented properties and methods**


![Utilities Data Classes](../media/utilities_data_classes.png)


## Supported event sources

Event Source | Data_class
------------------------------------------------- | ---------------------------------------------------------------------------------
[API Gateway Proxy](#api-gateway-proxy) | `APIGatewayProxyEvent`
[API Gateway Proxy event v2](#api-gateway-proxy-v2) | `APIGatewayProxyEventV2`
[AppSync Resolver](#appsync-resolver) | `AppSyncResolverEvent`
[CloudWatch Logs](#cloudwatch-logs) | `CloudWatchLogsEvent`
[Cognito User Pool](#cognito-user-pool) | Multiple available under `cognito_user_pool_event`
[Connect Contact Flow](#connect-contact-flow) | `ConnectContactFlowEvent`
[DynamoDB streams](#dynamodb-streams) | `DynamoDBStreamEvent`, `DynamoDBRecordEventName`
[EventBridge](#eventbridge) | `EventBridgeEvent`
[Kinesis Data Stream](#kinesis-streams) | `KinesisStreamEvent`
[S3](#s3) | `S3Event`
[SES](#ses) | `SESEvent`
[SNS](#sns) | `SNSEvent`
[SQS](#sqs) | `SQSEvent`


!!! info
    The examples provided below are far from exhaustive - the data classes themselves are designed to provide a form of
    documentation inherently (via autocompletion, types and docstrings).


### API Gateway Proxy

Typically, used for API Gateway REST API or HTTP API using v1 proxy event.

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

    def lambda_handler(event, context):
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        request_context = event.request_context
        identity = request_context.identity

        if 'helloworld' in event.path and event.http_method == 'GET':
            user = identity.user
            do_something_with(event.body, user)
    ```

### API Gateway Proxy v2

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2

    def lambda_handler(event, context):
        event: APIGatewayProxyEventV2 = APIGatewayProxyEventV2(event)
        request_context = event.request_context
        query_string_parameters = event.query_string_parameters

        if 'helloworld' in event.raw_path and request_context.http.method == 'POST':
            do_something_with(event.body, query_string_parameters)
    ```

### AppSync Resolver

Used when building a Lambda GraphQL Resolvers with [Amplify GraphQL Transform Library](https://docs.amplify.aws/cli/graphql-transformer/function){target="_blank"}
and can also be used for [AppSync Direct Lambda Resolvers](https://aws.amazon.com/blogs/mobile/appsync-direct-lambda/){target="_blank"}.

=== "app.py"

    ```python hl_lines="2-5 12 14 19 21 29-30"
    from aws_lambda_powertools.logging import Logger, correlation_paths
    from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import (
        AppSyncResolverEvent,
        AppSyncIdentityCognito
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
        logger.debug({
            "x-forwarded-for": x_forwarded_for,
            "username": identity.username
        })

        if event.type_name == "Merchant" and event.field_name == "locations":
            return get_locations(**event.arguments)

        raise ValueError(f"Unsupported field resolver: {event.field_name}")

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

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import CloudWatchLogsEvent
    from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import CloudWatchLogsDecodedData

    def lambda_handler(event, context):
        event: CloudWatchLogsEvent = CloudWatchLogsEvent(event)

        decompressed_log: CloudWatchLogsDecodedData = event.parse_logs_data
        log_events = decompressed_log.log_events
        for event in log_events:
            do_something_with(event.timestamp, event.message)
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

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import PostConfirmationTriggerEvent

    def lambda_handler(event, context):
        event: PostConfirmationTriggerEvent = PostConfirmationTriggerEvent(event)

        user_attributes = event.request.user_attributes
        do_something_with(user_attributes)
    ```

### Connect Contact Flow

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes.connect_contact_flow_event import (
        ConnectContactFlowChannel,
        ConnectContactFlowEndpointType,
        ConnectContactFlowEvent,
        ConnectContactFlowInitiationMethod,
    )

    def lambda_handler(event, context):
        event: ConnectContactFlowEvent = ConnectContactFlowEvent(event)
        assert event.contact_data.attributes == {"Language": "en-US"}
        assert event.contact_data.channel == ConnectContactFlowChannel.VOICE
        assert event.contact_data.customer_endpoint.endpoint_type == ConnectContactFlowEndpointType.TELEPHONE_NUMBER
        assert event.contact_data.initiation_method == ConnectContactFlowInitiationMethod.API
    ```

### DynamoDB Streams

The DynamoDB data class utility provides the base class for `DynamoDBStreamEvent`, a typed class for
attributes values (`AttributeValue`), as well as enums for stream view type (`StreamViewType`) and event type
(`DynamoDBRecordEventName`).

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
        DynamoDBStreamEvent,
        DynamoDBRecordEventName
    )

    def lambda_handler(event, context):
        event: DynamoDBStreamEvent = DynamoDBStreamEvent(event)

        # Multiple records can be delivered in a single event
        for record in event.records:
            if record.event_name == DynamoDBRecordEventName.MODIFY:
                do_something_with(record.dynamodb.new_image)
                do_something_with(record.dynamodb.old_image)
    ```

### EventBridge

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent

    def lambda_handler(event, context):
        event: EventBridgeEvent = EventBridgeEvent(event)
        do_something_with(event.detail)

    ```

### Kinesis streams

Kinesis events by default contain base64 encoded data. You can use the helper function to access the data either as json
or plain text, depending on the original payload.

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent

    def lambda_handler(event, context):
        event: KinesisStreamEvent = KinesisStreamEvent(event)
        kinesis_record = next(event.records).kinesis

        # if data was delivered as text
        data = kinesis_record.data_as_text()

        # if data was delivered as json
        data = kinesis_record.data_as_json()

        do_something_with(data)
    ```

### S3

=== "lambda_app.py"

    ```python
    from urllib.parse import unquote_plus
    from aws_lambda_powertools.utilities.data_classes import S3Event

    def lambda_handler(event, context):
        event: S3Event = S3Event(event)
        bucket_name = event.bucket_name

        # Multiple records can be delivered in a single event
        for record in event.records:
            object_key = unquote_plus(record.s3.get_object.key)

            do_something_with(f'{bucket_name}/{object_key}')
    ```

### SES

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import SESEvent

    def lambda_handler(event, context):
        event: SESEvent = SESEvent(event)

        # Multiple records can be delivered in a single event
        for record in event.records:
            mail = record.ses.mail
            common_headers = mail.common_headers

            do_something_with(common_headers.to, common_headers.subject)
    ```

### SNS

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import SNSEvent

    def lambda_handler(event, context):
        event: SNSEvent = SNSEvent(event)

        # Multiple records can be delivered in a single event
        for record in event.records:
            message = record.sns.message
            subject = record.sns.subject

            do_something_with(subject, message)
    ```

### SQS

=== "lambda_app.py"

    ```python
    from aws_lambda_powertools.utilities.data_classes import SQSEvent

    def lambda_handler(event, context):
        event: SQSEvent = SQSEvent(event)

        # Multiple records can be delivered in a single event
        for record in event.records:
            do_something_with(record.body)
    ```
