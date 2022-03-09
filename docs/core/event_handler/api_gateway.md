---
title: REST API
description: Core utility
---

Event handler for Amazon API Gateway REST and HTTP APIs, and Application Loader Balancer (ALB).

### Key Features

* Lightweight routing to reduce boilerplate for API Gateway REST/HTTP API and ALB
* Seamless support for CORS, binary and Gzip compression
* Integrates with [Data classes utilities](../../utilities/data_classes.md){target="_blank"} to easily access event and identity information
* Built-in support for Decimals JSON encoding
* Support for dynamic path expressions
* Router to allow for splitting up the handler across multiple files

## Getting started

### Required resources

You must have an existing [API Gateway Proxy integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html){target="_blank"} or [ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html){target="_blank"} configured to invoke your Lambda function. There is no additional permissions or dependencies required to use this utility.

This is the sample infrastructure for API Gateway we are using for the examples in this documentation.

```yaml title="AWS Serverless Application Model (SAM) example"
--8<-- "docs/examples/core/api_gateway/template.yml"
```

### Event Resolvers

Before you decorate your functions to handle a given path and HTTP method(s), you need to initialize a resolver.

A resolver will handle request resolution, include [one or more routers](#split-routes-with-router), and give you access to the current event via typed properties.

For resolvers, we provide: `APIGatewayRestResolver`, `APIGatewayHttpResolver`, and `ALBResolver`.

???+ info
    We will use `APIGatewayRestResolver` as the default across examples.

#### API Gateway REST API

When using Amazon API Gateway REST API to front your Lambda functions, you can use `APIGatewayRestResolver`.

Here's an example on how we can handle the `/hello` path.

???+ info
    We automatically serialize `Dict` responses as JSON, trim whitespace for compact responses, and set content-type to `application/json`.

=== "app.py"

    ```python hl_lines="2 7 10 13 20"
    --8<-- "docs/examples/core/api_gateway/app_rest_api.py"
    ```
=== "hello_event.json"

    This utility uses `path` and `httpMethod` to route to the right function. This helps make unit tests and local invocation easier too.

    ```json hl_lines="4-5"
    {
        "body": "hello",
        "resource": "/hello",
        "path": "/hello",
        "httpMethod": "GET",
        "isBase64Encoded": false,
        "queryStringParameters": {
            "foo": "bar"
        },
        "multiValueQueryStringParameters": {},
        "pathParameters": {
            "hello": "/hello"
        },
        "stageVariables": {},
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "max-age=0",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-Country": "US",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Custom User Agent String",
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https"
        },
        "multiValueHeaders": {},
        "requestContext": {
        "accountId": "123456789012",
        "resourceId": "123456",
        "stage": "Prod",
        "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
        "requestTime": "25/Jul/2020:12:34:56 +0000",
        "requestTimeEpoch": 1428582896000,
        "identity": {
            "cognitoIdentityPoolId": null,
            "accountId": null,
            "cognitoIdentityId": null,
            "caller": null,
            "accessKey": null,
            "sourceIp": "127.0.0.1",
            "cognitoAuthenticationType": null,
            "cognitoAuthenticationProvider": null,
            "userArn": null,
            "userAgent": "Custom User Agent String",
            "user": null
        },
        "path": "/Prod/hello",
        "resourcePath": "/hello",
        "httpMethod": "POST",
        "apiId": "1234567890",
        "protocol": "HTTP/1.1"
        }
    }
    ```

=== "response.json"

    ```json
    {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": "{\"message\":\"hello universe\"}",
        "isBase64Encoded": false
    }
    ```

#### API Gateway HTTP API

When using Amazon API Gateway HTTP API to front your Lambda functions, you can use `APIGatewayHttpResolver`.

???+ note
    Using HTTP API v1 payload? Use `APIGatewayRestResolver` instead. `APIGatewayHttpResolver` defaults to v2 payload.

Here's an example on how we can handle the `/hello` path.

```python hl_lines="2 7 20" title="Using HTTP API resolver"
--8<-- "docs/examples/core/api_gateway/app_http_api.py"
```

#### Application Load Balancer

When using Amazon Application Load Balancer to front your Lambda functions, you can use `ALBResolver`.

```python hl_lines="2 7 20" title="Using ALB resolver"
--8<-- "docs/examples/core/api_gateway/app_alb.py"
```

### Dynamic routes

You can use `/path/{dynamic_value}` when configuring dynamic URL paths. This allows you to define such dynamic value as part of your function signature.

=== "app.py"

    ```python hl_lines="10 12"
    --8<-- "docs/examples/core/api_gateway/app_dynamic_routes.py"
    ```

=== "sample_request.json"

    ```json
    {
        "resource": "/hello/{name}",
        "path": "/hello/lessa",
        "httpMethod": "GET",
        ...
    }
    ```

#### Nested routes

You can also nest paths as configured earlier in [our sample infrastructure](#required-resources): `/{message}/{name}`.

=== "app.py"

    ```python hl_lines="10 12"
    --8<-- "docs/examples/core/api_gateway/app_nested_routes.py"
    ```

=== "sample_request.json"

    ```json
    {
        "resource": "/{message}/{name}",
        "path": "/hi/michael",
        "httpMethod": "GET",
        ...
    }
    ```

#### Catch-all routes

???+ note
    We recommend having explicit routes whenever possible; use catch-all routes sparingly.

You can use a regex string to handle an arbitrary number of paths within a request, for example `.+`.

You can also combine nested paths with greedy regex to catch in between routes.

???+ warning
    We will choose the more explicit registered route that match incoming event.

=== "app.py"

    ```python hl_lines="6"
    --8<-- "docs/examples/core/api_gateway/app_catch_all_routes.py"
    ```

=== "sample_request.json"

    ```json
    {
        "resource": "/any/route/should/work",
        "path": "/any/route/should/work",
        "httpMethod": "GET",
        ...
    }
    ```
### HTTP Methods
You can use named decorators to specify the HTTP method that should be handled in your functions. As well as the
`get` method already shown above, you can use `post`, `put`, `patch`, `delete`, and `patch`.

=== "app.py"

    ```python hl_lines="10-11"
    --8<-- "docs/examples/core/api_gateway/app_http_methods.py"
    ```

=== "sample_request.json"

    ```json
    {
        "resource": "/hello/{name}",
        "path": "/hello/lessa",
        "httpMethod": "GET",
        ...
    }
    ```

If you need to accept multiple HTTP methods in a single function, you can use the `route` method and pass a list of
HTTP methods.

=== "app.py"

    ```python hl_lines="10-11"
    --8<-- "docs/examples/core/api_gateway/app_multi_http_methods.py"
    ```

=== "sample_request.json"

    ```json
    {
        "resource": "/hello/{name}",
        "path": "/hello/lessa",
        "httpMethod": "GET",
        ...
    }
    ```

???+ note
    It is usually better to have separate functions for each HTTP method, as the functionality tends to differ depending on which method is used.

### Accessing request details

By integrating with [Data classes utilities](../../utilities/data_classes.md){target="_blank"}, you have access to request details, Lambda context and also some convenient methods.

These are made available in the response returned when instantiating `APIGatewayRestResolver`, for example `app.current_event` and `app.lambda_context`.

#### Query strings and payload

Within `app.current_event` property, you can access query strings as dictionary via `query_string_parameters`, or by name via `get_query_string_value` method.

You can access the raw payload via `body` property, or if it's a JSON string you can quickly deserialize it via `json_body` property.

```python hl_lines="8-10 12" title="Accessing query strings, JSON payload, and raw payload"
--8<-- "docs/examples/core/api_gateway/app_query_string.py"
```

#### Headers

Similarly to [Query strings](#query-strings-and-payload), you can access headers as dictionary via `app.current_event.headers`, or by name via `get_header_value`.

```python hl_lines="8-9" title="Accessing HTTP Headers"
--8<-- "docs/examples/core/api_gateway/app_headers.py"
```

### Handling not found routes

By default, we return `404` for any unmatched route.

You can use **`not_found`** decorator to override this behaviour, and return a custom **`Response`**.

```python hl_lines="12 14 17" title="Handling not found"
--8<-- "docs/examples/core/api_gateway/app_not_found.py"
```

### Exception handling

You can use **`exception_handler`** decorator with any Python exception. This allows you to handle a common exception outside your route, for example validation errors.

```python hl_lines="11 16" title="Exception handling"
--8<-- "docs/examples/core/api_gateway/app_exception_handler.py"
```

### Raising HTTP errors

You can easily raise any HTTP Error back to the client using `ServiceError` exception.

???+ info
    If you need to send custom headers, use [Response](#fine-grained-responses) class instead.

Additionally, we provide pre-defined errors for the most popular ones such as HTTP 400, 401, 404, 500.

```python hl_lines="3-9 21 27 33 39 44" title="Raising common HTTP Status errors (4xx, 5xx)"
--8<-- "docs/examples/core/api_gateway/app_http_errors.py"
```

### Custom Domain API Mappings

When using Custom Domain API Mappings feature, you must use **`strip_prefixes`** param in the `APIGatewayRestResolver` constructor.

Scenario: You have a custom domain `api.mydomain.dev` and set an API Mapping `payment` to forward requests to your Payments API, the path argument will be `/payment/<your_actual_path>`.

This will lead to a HTTP 404 despite having your Lambda configured correctly. See the example below on how to account for this change.

=== "app.py"

    ```python hl_lines="7"
    --8<-- "docs/examples/core/api_gateway/app_custom_domain.py"
    ```

=== "sample_request.json"

    ```json
    {
        "resource": "/subscriptions/{subscription}",
        "path": "/payment/subscriptions/123",
        "httpMethod": "GET",
        ...
    }
    ```

???+ note
    After removing a path prefix with `strip_prefixes`, the new root path will automatically be mapped to the path argument of `/`.

	For example, when using `strip_prefixes` value of `/pay`, there is no difference between a request path of `/pay` and `/pay/`; and the path argument would be defined as `/`.

## Advanced

### CORS

You can configure CORS at the `APIGatewayRestResolver` constructor via `cors` parameter using the `CORSConfig` class.

This will ensure that CORS headers are always returned as part of the response when your functions match the path invoked.

=== "app.py"

    ```python hl_lines="8-9 12 18"
    --8<-- "docs/examples/core/api_gateway/app_cors.py"
    ```

=== "response.json"

    ```json
    {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://www.example.com",
            "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Amz-Date,X-Amz-Security-Token,X-Api-Key"
        },
        "body": "{\"message\":\"hello lessa\"}",
        "isBase64Encoded": false
    }
    ```

=== "response_no_cors.json"

    ```json
    {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": "{\"message\":\"hello lessa\"}",
        "isBase64Encoded": false
    }
    ```

???+ tip
    Optionally disable CORS on a per path basis with `cors=False` parameter.

#### Pre-flight

Pre-flight (OPTIONS) calls are typically handled at the API Gateway level as per [our sample infrastructure](#required-resources), no Lambda integration necessary. However, ALB expects you to handle pre-flight requests.

For convenience, we automatically handle that for you as long as you [setup CORS in the constructor level](#cors).

#### Defaults

For convenience, these are the default values when using `CORSConfig` to enable CORS:

???+ warning
    Always configure `allow_origin` when using in production.

Key | Value | Note
------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------
**[allow_origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin){target="_blank"}**: `str` | `*` | Only use the default value for development. **Never use `*` for production** unless your use case requires it
**[allow_headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers){target="_blank"}**: `List[str]` | `[Authorization, Content-Type, X-Amz-Date, X-Api-Key, X-Amz-Security-Token]` | Additional headers will be appended to the default list for your convenience
**[expose_headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Expose-Headers){target="_blank"}**: `List[str]` | `[]` | Any additional header beyond the [safe listed by CORS specification](https://developer.mozilla.org/en-US/docs/Glossary/CORS-safelisted_response_header){target="_blank"}.
**[max_age](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Max-Age){target="_blank"}**: `int` | `` | Only for pre-flight requests if you choose to have your function to handle it instead of API Gateway
**[allow_credentials](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials){target="_blank"}**: `bool` | `False` | Only necessary when you need to expose cookies, authorization headers or TLS client certificates.

### Fine grained responses

You can use the `Response` class to have full control over the response, for example you might want to add additional headers or set a custom Content-type.

=== "app.py"

    ```python hl_lines="13-18"
    --8<-- "docs/examples/core/api_gateway/app_response.py"
    ```

=== "response.json"

    ```json
    {
        "body": "{\"message\":\"I\'m a teapot\"}",
        "headers": {
            "Content-Type": "application/json",
            "X-Custom": "X-Value"
        },
        "isBase64Encoded": false,
        "statusCode": 418
    }
    ```

### Compress

You can compress with gzip and base64 encode your responses via `compress` parameter.

???+ warning
    The client must send the `Accept-Encoding` header, otherwise a normal response will be sent.

=== "app.py"

    ```python hl_lines="6 8"
    --8<-- "docs/examples/core/api_gateway/app_compress.py"
    ```

=== "sample_request.json"

    ```json
    {
        "headers": {
            "Accept-Encoding": "gzip"
        },
        "httpMethod": "GET",
        "path": "/hello",
        ...
    }
    ```

=== "response.json"

    ```json
    {
        "body": "H4sIAAAAAAACE6tWyk0tLk5MT1WyUspIzcnJVyjNyyxLLSpOVaoFANha8kEcAAAA",
        "headers": {
            "Content-Encoding": "gzip",
            "Content-Type": "application/json"
        },
        "isBase64Encoded": true,
        "statusCode": 200
    }
    ```

### Binary responses

For convenience, we automatically base64 encode binary responses. You can also use in combination with `compress` parameter if your client supports gzip.

Like `compress` feature, the client must send the `Accept` header with the correct media type.

???+ warning
    This feature requires API Gateway to configure binary media types, see [our sample infrastructure](#required-resources) for reference.

=== "app.py"

    ```python hl_lines="4 7 12"
    --8<-- "docs/examples/core/api_gateway/app_binary.py"
    ```

=== "logo.svg"

    ```xml
    <?xml version="1.0" encoding="utf-8"?>
    <!-- Generator: Adobe Illustrator 19.0.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
    <svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
            viewBox="0 0 304 182" style="enable-background:new 0 0 304 182;" xml:space="preserve">
    <style type="text/css">
        .st0{fill:#FFFFFF;}
        .st1{fill-rule:evenodd;clip-rule:evenodd;fill:#FFFFFF;}
    </style>
    <g>
        <path class="st0" d="M86.4,66.4c0,3.7,0.4,6.7,1.1,8.9c0.8,2.2,1.8,4.6,3.2,7.2c0.5,0.8,0.7,1.6,0.7,2.3c0,1-0.6,2-1.9,3l-6.3,4.2
            c-0.9,0.6-1.8,0.9-2.6,0.9c-1,0-2-0.5-3-1.4C76.2,90,75,88.4,74,86.8c-1-1.7-2-3.6-3.1-5.9c-7.8,9.2-17.6,13.8-29.4,13.8
            c-8.4,0-15.1-2.4-20-7.2c-4.9-4.8-7.4-11.2-7.4-19.2c0-8.5,3-15.4,9.1-20.6c6.1-5.2,14.2-7.8,24.5-7.8c3.4,0,6.9,0.3,10.6,0.8
            c3.7,0.5,7.5,1.3,11.5,2.2v-7.3c0-7.6-1.6-12.9-4.7-16c-3.2-3.1-8.6-4.6-16.3-4.6c-3.5,0-7.1,0.4-10.8,1.3c-3.7,0.9-7.3,2-10.8,3.4
            c-1.6,0.7-2.8,1.1-3.5,1.3c-0.7,0.2-1.2,0.3-1.6,0.3c-1.4,0-2.1-1-2.1-3.1v-4.9c0-1.6,0.2-2.8,0.7-3.5c0.5-0.7,1.4-1.4,2.8-2.1
            c3.5-1.8,7.7-3.3,12.6-4.5c4.9-1.3,10.1-1.9,15.6-1.9c11.9,0,20.6,2.7,26.2,8.1c5.5,5.4,8.3,13.6,8.3,24.6V66.4z M45.8,81.6
            c3.3,0,6.7-0.6,10.3-1.8c3.6-1.2,6.8-3.4,9.5-6.4c1.6-1.9,2.8-4,3.4-6.4c0.6-2.4,1-5.3,1-8.7v-4.2c-2.9-0.7-6-1.3-9.2-1.7
            c-3.2-0.4-6.3-0.6-9.4-0.6c-6.7,0-11.6,1.3-14.9,4c-3.3,2.7-4.9,6.5-4.9,11.5c0,4.7,1.2,8.2,3.7,10.6
            C37.7,80.4,41.2,81.6,45.8,81.6z M126.1,92.4c-1.8,0-3-0.3-3.8-1c-0.8-0.6-1.5-2-2.1-3.9L96.7,10.2c-0.6-2-0.9-3.3-0.9-4
            c0-1.6,0.8-2.5,2.4-2.5h9.8c1.9,0,3.2,0.3,3.9,1c0.8,0.6,1.4,2,2,3.9l16.8,66.2l15.6-66.2c0.5-2,1.1-3.3,1.9-3.9c0.8-0.6,2.2-1,4-1
            h8c1.9,0,3.2,0.3,4,1c0.8,0.6,1.5,2,1.9,3.9l15.8,67l17.3-67c0.6-2,1.3-3.3,2-3.9c0.8-0.6,2.1-1,3.9-1h9.3c1.6,0,2.5,0.8,2.5,2.5
            c0,0.5-0.1,1-0.2,1.6c-0.1,0.6-0.3,1.4-0.7,2.5l-24.1,77.3c-0.6,2-1.3,3.3-2.1,3.9c-0.8,0.6-2.1,1-3.8,1h-8.6c-1.9,0-3.2-0.3-4-1
            c-0.8-0.7-1.5-2-1.9-4L156,23l-15.4,64.4c-0.5,2-1.1,3.3-1.9,4c-0.8,0.7-2.2,1-4,1H126.1z M254.6,95.1c-5.2,0-10.4-0.6-15.4-1.8
            c-5-1.2-8.9-2.5-11.5-4c-1.6-0.9-2.7-1.9-3.1-2.8c-0.4-0.9-0.6-1.9-0.6-2.8v-5.1c0-2.1,0.8-3.1,2.3-3.1c0.6,0,1.2,0.1,1.8,0.3
            c0.6,0.2,1.5,0.6,2.5,1c3.4,1.5,7.1,2.7,11,3.5c4,0.8,7.9,1.2,11.9,1.2c6.3,0,11.2-1.1,14.6-3.3c3.4-2.2,5.2-5.4,5.2-9.5
            c0-2.8-0.9-5.1-2.7-7c-1.8-1.9-5.2-3.6-10.1-5.2L246,52c-7.3-2.3-12.7-5.7-16-10.2c-3.3-4.4-5-9.3-5-14.5c0-4.2,0.9-7.9,2.7-11.1
            c1.8-3.2,4.2-6,7.2-8.2c3-2.3,6.4-4,10.4-5.2c4-1.2,8.2-1.7,12.6-1.7c2.2,0,4.5,0.1,6.7,0.4c2.3,0.3,4.4,0.7,6.5,1.1
            c2,0.5,3.9,1,5.7,1.6c1.8,0.6,3.2,1.2,4.2,1.8c1.4,0.8,2.4,1.6,3,2.5c0.6,0.8,0.9,1.9,0.9,3.3v4.7c0,2.1-0.8,3.2-2.3,3.2
            c-0.8,0-2.1-0.4-3.8-1.2c-5.7-2.6-12.1-3.9-19.2-3.9c-5.7,0-10.2,0.9-13.3,2.8c-3.1,1.9-4.7,4.8-4.7,8.9c0,2.8,1,5.2,3,7.1
            c2,1.9,5.7,3.8,11,5.5l14.2,4.5c7.2,2.3,12.4,5.5,15.5,9.6c3.1,4.1,4.6,8.8,4.6,14c0,4.3-0.9,8.2-2.6,11.6
            c-1.8,3.4-4.2,6.4-7.3,8.8c-3.1,2.5-6.8,4.3-11.1,5.6C264.4,94.4,259.7,95.1,254.6,95.1z"/>
        <g>
            <path class="st1" d="M273.5,143.7c-32.9,24.3-80.7,37.2-121.8,37.2c-57.6,0-109.5-21.3-148.7-56.7c-3.1-2.8-0.3-6.6,3.4-4.4
                c42.4,24.6,94.7,39.5,148.8,39.5c36.5,0,76.6-7.6,113.5-23.2C274.2,133.6,278.9,139.7,273.5,143.7z"/>
            <path class="st1" d="M287.2,128.1c-4.2-5.4-27.8-2.6-38.5-1.3c-3.2,0.4-3.7-2.4-0.8-4.5c18.8-13.2,49.7-9.4,53.3-5
                c3.6,4.5-1,35.4-18.6,50.2c-2.7,2.3-5.3,1.1-4.1-1.9C282.5,155.7,291.4,133.4,287.2,128.1z"/>
        </g>
    </g>
    </svg>
    ```
=== "sample_request.json"

    ```json
    {
        "headers": {
            "Accept": "image/svg+xml"
        },
        "httpMethod": "GET",
        "path": "/logo",
        ...
    }
    ```

=== "response.json"

    ```json
    {
        "body": "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",
        "headers": {
            "Content-Type": "image/svg+xml"
        },
        "isBase64Encoded": true,
        "statusCode": 200
    }
    ```

### Debug mode

You can enable debug mode via `debug` param, or via `POWERTOOLS_EVENT_HANDLER_DEBUG` [environment variable](../../index.md#environment-variables).

This will enable full tracebacks errors in the response, print request and responses, and set CORS in development mode.

???+ danger
    This might reveal sensitive information in your logs and relax CORS restrictions, use it sparingly.

    It's best to use for local development only!

```python hl_lines="3" title="Enabling debug mode"
--8<-- "docs/examples/core/api_gateway/app_debug.py"
```

### Custom serializer

You can instruct API Gateway handler to use a custom serializer to best suit your needs, for example take into account Enums when serializing.

```python hl_lines="24-25 30" title="Using a custom JSON serializer for responses"
--8<-- "docs/examples/core/api_gateway/app_custom_serializer.py"
```

### Split routes with Router

As you grow the number of routes a given Lambda function should handle, it is natural to split routes into separate files to ease maintenance - That's where the `Router` feature is useful.

Let's assume you have `app.py` as your Lambda function entrypoint and routes in `users.py`, this is how you'd use the `Router` feature.

=== "users.py"

	We import **Router** instead of **APIGatewayRestResolver**; syntax wise is exactly the same.

    ```python hl_lines="5 8 12 15 21"
    --8<-- "docs/examples/core/api_gateway/users_split_routes.py"
    ```

=== "app.py"

	We use `include_router` method and include all user routers registered in the `router` global object.

	```python hl_lines="3 10-11"
    --8<-- "docs/examples/core/api_gateway/app_split_routes.py"
	```

#### Route prefix

In the previous example, `users.py` routes had a `/users` prefix. This might grow over time and become repetitive.

When necessary, you can set a prefix when including a router object. This means you could remove `/users` prefix in `users.py` altogether.

=== "app.py"

	```python hl_lines="9"
    --8<-- "docs/examples/core/api_gateway/app_route_prefix.py"
	```

=== "users.py"

    ```python hl_lines="11 16"
    --8<-- "docs/examples/core/api_gateway/users_route_prefix.py"
    ```

#### Sample layout

This sample project contains a Users function with two distinct set of routes, `/users` and `/health`. The layout optimizes for code sharing, no custom build tooling, and it uses [Lambda Layers](../../index.md#lambda-layer) to install Lambda Powertools.

=== "Project layout"

    ```python hl_lines="1 8 10 12-15"
    .
    ├── Pipfile                    # project app & dev dependencies; poetry, pipenv, etc.
    ├── Pipfile.lock
    ├── README.md
    ├── src
    │       ├── __init__.py
    │       ├── requirements.txt   # sam build detect it automatically due to CodeUri: src, e.g. pipenv lock -r > src/requirements.txt
    │       └── users
    │           ├── __init__.py
    │           ├── main.py       # this will be our users Lambda fn; it could be split in folders if we want separate fns same code base
    │           └── routers       # routers module
    │               ├── __init__.py
    │               ├── health.py # /users routes, e.g. from routers import users; users.router
    │               └── users.py  # /users routes, e.g. from .routers import users; users.router
    ├── template.yml              # SAM template.yml, CodeUri: src, Handler: users.main.lambda_handler
    └── tests
        ├── __init__.py
        ├── unit
        │   ├── __init__.py
        │   └── test_users.py     # unit tests for the users router
        │   └── test_health.py    # unit tests for the health router
        └── functional
            ├── __init__.py
            ├── conftest.py       # pytest fixtures for the functional tests
            └── test_main.py      # functional tests for the main lambda handler
    ```

=== "template.yml"

    ```yaml  hl_lines="22-23"
    --8<-- "docs/examples/core/api_gateway/layout/template.yml"
    ```

=== "src/users/main.py"

    ```python hl_lines="8 14-15"
    --8<-- "docs/examples/core/api_gateway/layout/main.py"
    ```

=== "src/users/routers/health.py"

    ```python hl_lines="4 6-7 10"
    --8<-- "docs/examples/core/api_gateway/layout/health.py"
    ```

=== "tests/functional/test_users.py"

    ```python  hl_lines="3"
    --8<-- "docs/examples/core/api_gateway/layout/test_users.py"
    ```

### Considerations

This utility is optimized for fast startup, minimal feature set, and to quickly on-board customers familiar with frameworks like Flask — it's not meant to be a fully fledged framework.

Event Handler naturally leads to a single Lambda function handling multiple routes for a given service, which can be eventually broken into multiple functions.

Both single (monolithic) and multiple functions (micro) offer different set of trade-offs worth knowing.

???+ tip
    TL;DR. Start with a monolithic function, add additional functions with new handlers, and possibly break into micro functions if necessary.

#### Monolithic function

![Monolithic function sample](./../../media/monolithic-function.png)

A monolithic function means that your final code artifact will be deployed to a single function. This is generally the best approach to start.

_**Benefits**_

* **Code reuse**. It's easier to reason about your service, modularize it and reuse code as it grows. Eventually, it can be turned into a standalone library.
* **No custom tooling**. Monolithic functions are treated just like normal Python packages; no upfront investment in tooling.
* **Faster deployment and debugging**. Whether you use all-at-once, linear, or canary deployments, a monolithic function is a single deployable unit. IDEs like PyCharm and VSCode have tooling to quickly profile, visualize, and step through debug any Python package.

_**Downsides**_

* **Cold starts**. Frequent deployments and/or high load can diminish the benefit of monolithic functions depending on your latency requirements, due to [Lambda scaling model](https://docs.aws.amazon.com/lambda/latest/dg/invocation-scaling.html){target="_blank"}. Always load test to pragmatically balance between your customer experience and development cognitive load.
* **Granular security permissions**. The micro function approach enables you to use fine-grained permissions & access controls, separate external dependencies & code signing at the function level. Conversely, you could have multiple functions while duplicating the final code artifact in a monolithic approach.
    - Regardless, least privilege can be applied to either approaches.
* **Higher risk per deployment**. A misconfiguration or invalid import can cause disruption if not caught earlier in automated testing. Multiple functions can mitigate misconfigurations but they would still share the same code artifact. You can further minimize risks with multiple environments in your CI/CD pipeline.

#### Micro function

![Micro function sample](./../../media/micro-function.png)

A micro function means that your final code artifact will be different to each function deployed. This is generally the approach to start if you're looking for fine-grain control and/or high load on certain parts of your service.

_**Benefits**_

* **Granular scaling**. A micro function can benefit from the [Lambda scaling model](https://docs.aws.amazon.com/lambda/latest/dg/invocation-scaling.html){target="_blank"} to scale differently depending on each part of your application. Concurrency controls and provisioned concurrency can also be used at a granular level for capacity management.
* **Discoverability**. Micro functions are easier do visualize when using distributed tracing. Their high-level architectures can be self-explanatory, and complexity is highly visible — assuming each function is named to the business purpose it serves.
* **Package size**. An independent function can be significant smaller (KB vs MB) depending on external dependencies it require to perform its purpose. Conversely, a monolithic approach can benefit from [Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/invocation-layers.html){target="_blank"} to optimize builds for external dependencies.

_**Downsides**_

* **Upfront investment**. Python ecosystem doesn't use a bundler — you need a custom build tooling to ensure each function only has what it needs and account for [C bindings for runtime compatibility](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html){target="_blank"}. Operations become more elaborate — you need to standardize tracing labels/annotations, structured logging, and metrics to pinpoint root causes.
    - Engineering discipline is necessary for both approaches. Micro-function approach however requires further attention in consistency as the number of functions grow, just like any distributed system.
* **Harder to share code**. Shared code must be carefully evaluated to avoid unnecessary deployments when that changes. Equally, if shared code isn't a library,
your development, building, deployment tooling need to accommodate the distinct layout.
* **Slower safe deployments**. Safely deploying multiple functions require coordination — AWS CodeDeploy deploys and verifies each function sequentially. This increases lead time substantially (minutes to hours) depending on the deployment strategy you choose. You can mitigate it by selectively enabling it in prod-like environments only, and where the risk profile is applicable.
    - Automated testing, operational and security reviews are essential to stability in either approaches.

## Testing your code

You can test your routes by passing a proxy event request where `path` and `httpMethod`.

=== "test_app.py"

    ```python hl_lines="20-26"
    --8<-- "docs/examples/core/api_gateway/test_app.py"
    ```

=== "app.py"

    ```python
    --8<-- "docs/examples/core/api_gateway/app_test.py"
    ```

## FAQ

**What's the difference between this utility and frameworks like Chalice?**

Chalice is a full featured microframework that manages application and infrastructure. This utility, however, is largely focused on routing to reduce boilerplate and expects you to setup and manage infrastructure with your framework of choice.

That said, [Chalice has native integration with Lambda Powertools](https://aws.github.io/chalice/topics/middleware.html){target="_blank"} if you're looking for a more opinionated and web framework feature set.

**What happened to `ApiGatewayResolver`?**

It's been superseded by more explicit resolvers like `APIGatewayRestResolver`, `APIGatewayHttpResolver`, and `ALBResolver`.

`ApiGatewayResolver` handled multiple types of event resolvers for convenience via `proxy_type` param. However,
it made it impossible for static checkers like Mypy and IDEs IntelliSense to know what properties a `current_event` would have due to late bound resolution.

This provided a suboptimal experience for customers not being able to find all properties available besides common ones between API Gateway REST, HTTP, and ALB - while manually annotating `app.current_event` would work it is not the experience we want to provide to customers.

`ApiGatewayResolver` will be deprecated in v2 and have appropriate warnings as soon as we have a v2 draft.
