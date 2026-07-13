---
title: API Gateway WebSocket APIs
description: Core utility
status: new
---

Event Handler for Amazon API Gateway WebSocket APIs.

## Key Features

* Route WebSocket events by route key with dedicated `$connect`, `$disconnect`, and `$default` decorators
* Automatic response normalization to the `statusCode`/`body` shape API Gateway expects
* Accept or reject connections from your `$connect` handler with a status code
* Exception handling with a safety net that prevents stack traces from reaching connected clients
* No dependencies beyond the standard library — routing works with the core Powertools for AWS package

## Terminology

**[WebSocket API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html){target="_blank"}**. An API Gateway API type that maintains a persistent, bidirectional connection between clients and your backend. API Gateway manages the connections; your Lambda function receives one event per client message or lifecycle change.

**Route key**. The value API Gateway uses to select which route (and backend integration) handles a message. Lifecycle events use the predefined `$connect`, `$disconnect`, and `$default` route keys; your API can define custom route keys for application messages.

**[Route selection expression](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-develop-routes.html){target="_blank"}**. An API-level expression, commonly `$request.body.action`, that extracts the route key from each incoming message. Messages that don't match any custom route fall through to `$default`.

**Connection ID**. A unique identifier API Gateway assigns to each connection. After `$connect`, it is the only identity a message carries unless a Lambda authorizer is configured — treat it as the session key and look up anything else you need against it.

**[Route response](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-route-response.html){target="_blank"}**. Opt-in configuration that makes API Gateway deliver your handler's returned body back to the calling client. Without a route response on the route, returned bodies are discarded.

**[Lambda authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-lambda-auth.html){target="_blank"}**. An optional authorization step you configure on your API's `$connect` route. API Gateway invokes it before your handler; on success, it stores the authorizer's output with the connection and injects it into every subsequent invocation.

## Getting started

### Required resources

You need an API Gateway WebSocket API with its routes integrated with your Lambda function. The template below wires `$connect`, `$disconnect`, `$default`, and a custom `orderUpdate` route to a single function.

???+ warning "Returned bodies need a route response"
    A handler's returned body reaches the calling client only on routes with a **route response** configured. Without it, API Gateway silently discards the body. The template configures route responses on `orderUpdate` and `$default` so the replies in the examples below actually reach the client.

=== "getting_started_with_websocket_api.yaml"

    ```yaml hl_lines="27 50-80"
    --8<-- "examples/event_handler_api_gateway_websocket/sam/getting_started_with_websocket_api.yaml"
    ```

### Route decorators

Register handlers with `@app.on_connect()`, `@app.on_disconnect()`, `@app.on_default()`, or `@app.route("yourRouteKey")` for custom route keys. Handlers take no arguments; they access the request through `app.current_event` and return a value that becomes the Lambda response.

Route keys are matched exactly — API Gateway resolves the route key through the route selection expression before invoking your function, so there is nothing to pattern-match.

=== "getting_started_with_connect.py"

    ```python hl_lines="6 9 12 16"
    --8<-- "examples/event_handler_api_gateway_websocket/src/getting_started_with_connect.py"
    ```

    1. Headers and cookies are only available on `$connect` — later messages carry only the connection ID.
    2. Returning a non-2xx status code rejects the WebSocket upgrade.
    3. `None` normalizes to `{"statusCode": 200}`, accepting the connection.

=== "getting_started_with_disconnect.py"

    ```python hl_lines="6 9"
    --8<-- "examples/event_handler_api_gateway_websocket/src/getting_started_with_disconnect.py"
    ```

    1. `$disconnect` is delivered on a best-effort basis, including for connections whose `$connect` was rejected — don't assume your connect handler accepted this connection.

=== "getting_started_with_custom_route.py"

    ```python hl_lines="4 7 13"
    --8<-- "examples/event_handler_api_gateway_websocket/src/getting_started_with_custom_route.py"
    ```

    1. With the route selection expression `$request.body.action`, this handles messages like `{"action": "orderUpdate", "orderId": 123}`.
    2. Messages whose route key doesn't match any route fall through to `$default`.

### Response format

The resolver normalizes your handler's return value into the response shape API Gateway expects. Return a plain value, or a 2-tuple to set the status code:

| Handler returns | Lambda response |
| --------------- | --------------- |
| `None` | `{"statusCode": 200}` |
| `str` | `{"statusCode": 200, "body": <str>}` |
| `dict` / `list` | `{"statusCode": 200, "body": json.dumps(value)}` |
| 2-tuple `(value, status_code)` | status code from the tuple; body from `value` per the rules above |

A returned dict is always body content — it is never inspected for a `statusCode` key.

???+ note "`None` maps to 200, not an empty response"
    Unlike the REST resolver, `None` returns `{"statusCode": 200}` because `$connect` requires a status code, and accepting the connection is the only sensible default.

The status code has different effects depending on the route:

* **`$connect`**: the status code decides the connection — 2xx accepts the WebSocket upgrade, anything else rejects it.
* **All other routes**: the body is delivered back to the client only when the route has a route response configured, and a non-2xx status code does **not** drop the connection.

## Advanced

### Exception handling

Register handlers for specific exception types with `@app.exception_handler`; it also accepts a list of types, and lookup respects inheritance. The handler receives the exception, and its return value goes through the same [response normalization](#response-format).

=== "working_with_exception_handling.py"

    ```python hl_lines="9 12 19"
    --8<-- "examples/event_handler_api_gateway_websocket/src/working_with_exception_handling.py"
    ```

    1. Also accepts a list of exception types, and matches subclasses of the registered type.
    2. The handler's return value goes through the same normalization as route handler returns.

???+ note "Unhandled exceptions never reach the client"
    An exception with no registered handler is logged and becomes a bare `{"statusCode": 500}`. If it propagated to the Lambda runtime instead, the runtime's error response — exception type, message, and stack trace — would be delivered to the connected client.

## Testing your code

Test your handlers by passing a WebSocket event payload to `app.resolve()` — no mocks of API Gateway needed.

=== "getting_started_with_testing.py"

    ```python
    --8<-- "examples/event_handler_api_gateway_websocket/src/getting_started_with_testing.py"
    ```

=== "getting_started_with_testing_event.json"

    ```json
    --8<-- "examples/event_handler_api_gateway_websocket/src/getting_started_with_testing_event.json"
    ```
