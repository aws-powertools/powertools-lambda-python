---
title: AppSync Events
description: Core utility
status: new
---

Event Handler for AWS AppSync real-time events.

```mermaid
stateDiagram-v2
    direction LR
    EventSource: AppSync Events
    EventHandlerResolvers: Publish & Subscribe events
    LambdaInit: Lambda invocation
    EventHandler: Event Handler
    EventHandlerResolver: Route event based on namespace/channel
    YourLogic: Run your registered handler function
    EventHandlerResolverBuilder: Adapts response to AppSync contract
    LambdaResponse: Lambda response

    state EventSource {
        EventHandlerResolvers
    }

    EventHandlerResolvers --> LambdaInit

    LambdaInit --> EventHandler
    EventHandler --> EventHandlerResolver

    state EventHandler {
        [*] --> EventHandlerResolver: app.resolve(event, context)
        EventHandlerResolver --> YourLogic
        YourLogic --> EventHandlerResolverBuilder
    }

    EventHandler --> LambdaResponse
```

## Key Features

* Easily handle publish and subscribe events with dedicated handler methods
* Automatic routing based on namespace and channel patterns
* Support for wildcard patterns to create catch-all handlers
* Process events in parallel corontrol aggregation for batch processing
* Graceful error handling for individual events

## Terminology

**[AWS AppSync Events](https://docs.aws.amazon.com/appsync/latest/eventapi/event-api-welcome.html){target="_blank"}**. A service that enables you to quickly build secure, scalable real-time WebSocket APIs without managing infrastructure or writing API code.

It handles connection management, message broadcasting, authentication, and monitoring, reducing time to market and operational costs.

## Getting started

???+ tip "Tip: New to AppSync Real-time API?"
    Visit [AWS AppSync Real-time documentation](https://docs.aws.amazon.com/appsync/latest/eventapi/event-api-getting-started.html){target="_blank"} to understand how to set up subscriptions and pub/sub messaging.

### Required resources

You must have an existing AppSync Events API with real-time capabilities enabled and IAM permissions to invoke your Lambda function. That said, there are no additional permissions required to use Event Handler as routing requires no dependency (_standard library_).

### AppSync request and response format

AppSync Events uses a specific event format for Lambda requests and responses. In most scenarios, Powertools for AWS simplifies this interaction by automatically formatting resolver returns to match the expected AppSync response structure.

=== "payload_request.json"

    ```python hl_lines="5 10 12"
    --8<-- "examples/event_handler_appsync_events/src/payload_request.json"
    ```

=== "payload_response.json"

    ```python hl_lines="5 10 12"
    --8<-- "examples/event_handler_appsync_events/src/payload_response.json"
    ```

=== "payload_response_with_error.json"

    ```python hl_lines="5 10 12"
    --8<-- "examples/event_handler_appsync_events/src/payload_response_with_error.json"
    ```

=== "payload_response_fail_request.json"

    ```python hl_lines="5 10 12"
    --8<-- "examples/event_handler_appsync_events/src/payload_response_fail_request.json"
    ```

#### Events response with error

When processing events with Lambda, you can return errors to AppSync in three ways:

* **Item specific error:** Return an `error` key within each individual item's response. AppSync Events expects this format for item-specific errors.
* **Fail entire request:** Return a JSON object with a top-level `error` key. This signals a general failure, and AppSync treats the entire request as unsuccessful.
* **Unauthorized exception**: Raise the **UnauthorizedException** exception to reject a subscribe or publish request with HTTP 403.

### Resolver decorator

???+ important
    The event handler automatically parses the incoming event data and invokes the appropriate handler based on the namespace/channel pattern you register.

You can define your handlers for different event types using the `app.on_publish()`, `app.async_on_publish()`, and `app.on_subscribe()` methods.

=== "getting_started_with_publish_events.py"

    ```python hl_lines="5 10 12"
    --8<-- "examples/event_handler_appsync_events/src/getting_started_with_publish_events.py"
    ```

=== "getting_started_with_subscribe_events.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/getting_started_with_subscribe_events.py"
    ```

## Advanced

### Wildcard patterns and handler precedence

You can use wildcard patterns to create catch-all handlers for multiple channels or namespaces. This is particularly useful for centralizing logic that applies to multiple channels.

When an event matches with multiple handlers, the most specific pattern takes precedence.

???+ note "Supported wildcard patterns"
    Only the following patterns are supported:

    * `/namespace/*` - Matches all channels in the specified namespace
    * `/*` - Matches all channels in all namespaces

    Patterns like `/namespace/channel*` or `/namespace/*/subpath` are not supported.

    More specific routes will always take precedence over less specific ones. For example, `/default/channel1` will take precedence over `/default/*`, which will take precedence over `/*`.

=== "working_with_wildcard_resolvers.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_wildcard_resolvers.py"
    ```

If the event doesn't match any registered handler, the Event Handler will log a warning and skip processing the event.

### Aggregated processing

???+ note "Aggregate Processing"
    When `aggregate=True`, your handler receives a list of all events, requiring you to manage the response format. Ensure your response includes results for each event in the expected [AppSync Request and Response Format](#appsync-request-and-response-format).

In some scenarios, you might want to process all events for a channel as a batch rather than individually. This is useful when you need to:

* Optimize database operations by making a single batch query
* Ensure all events are processed together or not at all
* Apply custom error handling logic for the entire batch

You can enable this with the `aggregate` parameter:

=== "working_with_aggregated_events.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_aggregated_events.py"
    ```

### Handling errors

You can filter or reject events by raising exceptions in your resolvers or by formatting the payload according to the expected response structure. This instructs AppSync not to propagate that specific message, so subscribers will not receive it.

#### Handling errors with individual items

When processing items individually with `aggregate=False`, you can raise an exception to fail a specific message. When this happens, the Event Handler will catch it and include the exception name and message in the response.

=== "working_with_error_handling.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling.py"
    ```

=== "working_with_error_handling_response.json"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling_response.json"
    ```

#### Handling errors with batch of items

When processing batch of items with `aggregate=True`, you must format the payload according the expected response.

=== "working_with_error_handling_multiple.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling_multiple.py"
    ```

=== "working_with_error_handling_response.json"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling_response.json"
    ```

If instead you want to fail the entire batch, you can throw an exception. This will cause the Event Handler to return an error response to AppSync and fail the entire batch.

=== "working_with_error_handling_multiple.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling_multiple.py"
    ```

=== "working_with_error_handling_response.json"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling_response.json"
    ```

#### Authorization control

!!! warning "Raising `UnauthorizedException` will cause the Lambda invocation to fail."

You can also do content based authorization for channel by raising the `UnauthorizedException` exception. This can cause two situations:

* **When working with publish events** Powertools for AWS stop processing messages and subscribers will not receive any message.
* **When working with subscribe events** the subscription won't be established.

=== "working_with_error_handling.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling.py"
    ```

=== "working_with_error_handling_response.json"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_error_handling_response.json"
    ```

### Processing events with async resolvers

Use the `@app.async_on_publish()` decorator to process events asynchronously.

We use `asyncio` module to support async functions, and we ensure reliable execution by managing the event loop.

???+ note "Events order and AppSync Events"
    AppSync does not rely on event order. As long as each event includes the original `id`, AppSync processes them correctly regardless of the order in which they are received.

=== "working_with_async_resolvers.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/working_with_async_resolvers.py"
    ```

### Accessing Lambda context and event

You can access to the original Lambda event or context for additional information. These are accessible via the app instance:

=== "accessing_event_and_context.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/accessing_event_and_context.py"
    ```

## Event Handler workflow

### Working with single items

<center>
```mermaid
sequenceDiagram
    participant Client
    participant AppSync
    participant Lambda
    participant EventHandler
    note over Client,EventHandler: Individual Event Processing (aggregate=False)
    Client->>+AppSync: Send multiple events to channel
    AppSync->>+Lambda: Invoke Lambda with batch of events
    Lambda->>+EventHandler: Process events with aggregate=False
    loop For each event in batch
        EventHandler->>EventHandler: Process individual event
    end
    EventHandler-->>-Lambda: Return array of processed events
    Lambda-->>-AppSync: Return event-by-event responses
    AppSync-->>-Client: Report individual event statuses
```
</center>

### Working with aggregated items

<center>
```mermaid
sequenceDiagram
    participant Client
    participant AppSync
    participant Lambda
    participant EventHandler
    note over Client,EventHandler: Aggregate Processing Workflow
    Client->>+AppSync: Send multiple events to channel
    AppSync->>+Lambda: Invoke Lambda with batch of events
    Lambda->>+EventHandler: Process events with aggregate=True
    EventHandler->>EventHandler: Batch of events
    EventHandler->>EventHandler: Process entire batch at once
    EventHandler->>EventHandler: Format response for each event
    EventHandler-->>-Lambda: Return aggregated results
    Lambda-->>-AppSync: Return success responses
    AppSync-->>-Client: Confirm all events processed
```
</center>

### Authorization fails for publish

<center>
```mermaid
sequenceDiagram
    participant Client
    participant AppSync
    participant Lambda
    participant EventHandler
    note over Client,EventHandler: Publish Event Authorization Flow
    Client->>AppSync: Publish message to channel
    AppSync->>Lambda: Invoke Lambda with publish event
    Lambda->>EventHandler: Process publish event
    alt Authorization Failed
        EventHandler->>EventHandler: Authorization check fails
        EventHandler->>Lambda: Raise UnauthorizedException
        Lambda->>AppSync: Return error response
        AppSync--xClient: Message not delivered
        AppSync--xAppSync: No distribution to subscribers
    else Authorization Passed
        EventHandler->>Lambda: Return successful response
        Lambda->>AppSync: Return processed event
        AppSync->>Client: Acknowledge message
        AppSync->>AppSync: Distribute to subscribers
    end
```
</center>

### Authorization fails for subscribe

<center>
```mermaid
sequenceDiagram
    participant Client
    participant AppSync
    participant Lambda
    participant EventHandler
    note over Client,EventHandler: Subscribe Event Authorization Flow
    Client->>AppSync: Request subscription to channel
    AppSync->>Lambda: Invoke Lambda with subscribe event
    Lambda->>EventHandler: Process subscribe event
    alt Authorization Failed
        EventHandler->>EventHandler: Authorization check fails
        EventHandler->>Lambda: Raise UnauthorizedException
        Lambda->>AppSync: Return error response
        AppSync--xClient: Subscription denied (HTTP 403)
    else Authorization Passed
        EventHandler->>Lambda: Return successful response
        Lambda->>AppSync: Return authorization success
        AppSync->>Client: Subscription established
    end
```
</center>

## Testing your code

You can test your event handlers by passing a mocked or actual AppSync Events Lambda event.

### Testing publish events

=== "getting_started_with_testing_publish.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/getting_started_with_testing_publish.py"
    ```

=== "getting_started_with_testing_publish_event.json"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/getting_started_with_testing_publish_event.json"
    ```

### Testing subscribe events

=== "getting_started_with_testing_subscribe.py"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/getting_started_with_testing_subscribe.py"
    ```

=== "getting_started_with_testing_subscribe_event.json"

    ```python hl_lines="5 6 13"
    --8<-- "examples/event_handler_appsync_events/src/getting_started_with_testing_subscribe_event.json"
    ```
