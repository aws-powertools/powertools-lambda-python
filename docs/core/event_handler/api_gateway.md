---
title: API Gateway
description: Core utility
---

Event handler for Amazon API Gateway REST/HTTP APIs and Application Loader Balancer (ALB).

!!! todo "Change proxy types enum to match PascalCase"

!!! todo "Update `route` methods to include an example in docstring to improve developer experience"

### Key Features

* Lightweight routing to reduce boilerplate for API Gateway REST/HTTP API and ALB
* Seamless support for CORS, binary and Gzip compression
* Integrates with [Data classes utilities](../../utilities/data_classes.md){target="_blank"} to easily access event and identity information
* Built-in support for Decimals JSON encoding
* Support for dynamic path expressions

## Getting started

### Required resources

You must have an existing [API Gateway Proxy integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html){target="_blank"} or [ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html){target="_blank"} configured to invoke your Lambda function. There is no additional permissions or dependencies required to use this utility.

This is the sample infrastructure we are using for the initial examples in this section.

=== "template.yml"

	```yaml
	AWSTemplateFormatVersion: '2010-09-09'
	Transform: AWS::Serverless-2016-10-31
	Description: Hello world event handler API Gateway

	Globals:
      Function:
        Timeout: 5
        Runtime: python3.8
        Tracing: Active
          Environment:
            Variables:
              LOG_LEVEL: INFO
              POWERTOOLS_LOGGER_SAMPLE_RATE: 0.1
              POWERTOOLS_LOGGER_LOG_EVENT: true
              POWERTOOLS_METRICS_NAMESPACE: MyServerlessApplication
              POWERTOOLS_SERVICE_NAME: hello

	Resources:
	  HelloWorldFunction:
        Type: AWS::Serverless::Function
        Properties:
          Handler: app.lambda_handler
          CodeUri: hello_world
          Description: Hello World function
			Events:
				HelloUniverse:
				  Type: Api
					Properties:
					  Path: /hello
					  Method: GET
				HelloYou:
				  Type: Api
					Properties:
					  Path: /hello/{name}
					  Method: GET

	Outputs:
      HelloWorldApigwURL:
        Description: "API Gateway endpoint URL for Prod environment for Hello World Function"
        Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello"

    HelloWorldFunction:
        Description: "Hello World Lambda Function ARN"
        Value: !GetAtt HelloWorldFunction.Arn
	```

### Resolver decorator


### Path expressions

### CORS

## Advanced

### Fine grained responses

### Binary responses

### Testing your code

## Examples

> TODO - Break on into smaller examples

### All in one example

=== "app.py"

```python
from decimal import Decimal
import json
from typing import Dict, Tuple

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    CORSConfig,
    ProxyEventType,
    Response,
)

tracer = Tracer()
# Other supported proxy_types: "APIGatewayProxyEvent", "APIGatewayProxyEventV2", "ALBEvent"
app = ApiGatewayResolver(
    proxy_type=ProxyEventType.http_api_v1,
    cors=CORSConfig(
        allow_origin="https://www.example.com/",
        expose_headers=["x-exposed-response-header"],
        allow_headers=["x-custom-request-header"],
        max_age=100,
        allow_credentials=True,
    )
)

@app.get("/foo", compress=True)
def get_foo() -> Tuple[int, str, str]:
    # Matches on http GET and proxy path "/foo"
    # and return status code: 200, content-type: text/html and body: Hello
    return 200, "text/html", "Hello"

@app.get("/logo.png")
def get_logo() -> Tuple[int, str, bytes]:
    # Base64 encodes the return bytes body automatically
    logo: bytes = load_logo()
    return 200, "image/png", logo

@app.post("/make_foo", cors=True)
def make_foo() -> Tuple[int, str, str]:
    # Matches on http POST and proxy path "/make_foo"
    post_data: dict = app. current_event.json_body
    return 200, "application/json", json.dumps(post_data["value"])

@app.delete("/delete/<uid>")
def delete_foo(uid: str) -> Tuple[int, str, str]:
    # Matches on http DELETE and proxy path starting with "/delete/"
    assert isinstance(app.current_event, APIGatewayProxyEvent)
    assert app.current_event.request_context.authorizer.claims is not None
    assert app.current_event.request_context.authorizer.claims["username"] == "Mike"
    return 200, "application/json", json.dumps({"id": uid})

@app.get("/hello/<username>")
def hello_user(username: str) -> Tuple[int, str, str]:
    return 200, "text/html", f"Hello {username}!"

@app.get("/rest")
def rest_fun() -> Dict:
    # Returns a statusCode: 200, Content-Type: application/json and json.dumps dict
    # and handles the serialization of decimals to json string
    return {"message": "Example", "second": Decimal("100.01")}

@app.get("/foo3")
def foo3() -> Response:
    return Response(
        status_code=200,
        content_type="application/json",
        headers={"custom-header": "value"},
        body=json.dumps({"message": "Foo3"}),
    )

@tracer.capture_lambda_handler
def lambda_handler(event, context) -> Dict:
    return app.resolve(event, context)
```

### Compress examples

=== "app.py"

    ```python
    from aws_lambda_powertools.event_handler.api_gateway import (
        ApiGatewayResolver
    )

    app = ApiGatewayResolver()

    @app.get("/foo", compress=True)
    def get_foo() -> Tuple[int, str, str]:
        # Matches on http GET and proxy path "/foo"
        # and return status code: 200, content-type: text/html and body: Hello
        return 200, "text/html", "Hello"
    ```

=== "GET /foo: request"
    ```json
    {
        "headers": {
            "Accept-Encoding": "gzip"
        },
        "httpMethod": "GET",
        "path": "/foo"
    }
    ```

=== "GET /foo: response"

    ```json
    {
        "body": "H4sIAAAAAAACE/NIzcnJBwCCidH3BQAAAA==",
        "headers": {
            "Content-Encoding": "gzip",
            "Content-Type": "text/html"
        },
        "isBase64Encoded": true,
        "statusCode": 200
    }
    ```

### CORS examples

=== "app.py"

    ```python
    from aws_lambda_powertools.event_handler.api_gateway import (
        ApiGatewayResolver,
        CORSConfig,
    )

    app = ApiGatewayResolver(
        proxy_type=ProxyEventType.http_api_v1,
        cors=CORSConfig(
            allow_origin="https://www.example.com/",
            expose_headers=["x-exposed-response-header"],
            allow_headers=["x-custom-request-header"],
            max_age=100,
            allow_credentials=True,
        )
    )

    @app.post("/make_foo", cors=True)
    def make_foo() -> Tuple[int, str, str]:
        # Matches on http POST and proxy path "/make_foo"
        post_data: dict = app. current_event.json_body
        return 200, "application/json", json.dumps(post_data["value"])
    ```

=== "OPTIONS /make_foo"

    ```json
    {
        "httpMethod": "OPTIONS",
        "path": "/make_foo"
    }
    ```

=== "<< OPTIONS /make_foo"

    ```json
    {
        "body": null,
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Amz-Date,X-Amz-Security-Token,X-Api-Key,x-custom-request-header",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
            "Access-Control-Allow-Origin": "https://www.example.com/",
            "Access-Control-Expose-Headers": "x-exposed-response-header",
            "Access-Control-Max-Age": "100"
        },
        "isBase64Encoded": false,
        "statusCode": 204
    }
    ```

=== "POST /make_foo"

    ```json
    {
        "body": "{\"value\": \"Hello World\"}",
        "httpMethod": "POST",
        "path": "/make_foo"
    }
    ```

=== "<< POST /make_foo"

    ```json
    {
        "body": "\"Hello World\"",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Amz-Date,X-Amz-Security-Token,X-Api-Key,x-custom-request-header",
            "Access-Control-Allow-Origin": "https://www.example.com/",
            "Access-Control-Expose-Headers": "x-exposed-response-header",
            "Access-Control-Max-Age": "100",
            "Content-Type": "application/json"
        },
        "isBase64Encoded": false,
        "statusCode": 200
    }
    ```

### Simple rest example

=== "app.py"

    ```python
    from aws_lambda_powertools.event_handler.api_gateway import (
        ApiGatewayResolver
    )

    app = ApiGatewayResolver()

    @app.get("/rest")
    def rest_fun() -> Dict:
        # Returns a statusCode: 200, Content-Type: application/json and json.dumps dict
        # and handles the serialization of decimals to json string
        return {"message": "Example", "second": Decimal("100.01")}
    ```

=== "GET /rest: request"

    ```json
    {
        "httpMethod": "GET",
        "path": "/rest"
    }
    ```

=== "GET /rest: response"

    ```json
    {
        "body": "{\"message\":\"Example\",\"second\":\"100.01\"}",
        "headers": {
            "Content-Type": "application/json"
        },
        "isBase64Encoded": false,
        "statusCode": 200
    }
    ```

### Custom response

=== "app.py"

    ```python
    from aws_lambda_powertools.event_handler.api_gateway import (
        ApiGatewayResolver
    )

    app = ApiGatewayResolver()

    @app.get("/foo3")
    def foo3() -> Response:
        return Response(
            status_code=200,
            content_type="application/json",
            headers={"custom-header": "value"},
            body=json.dumps({"message": "Foo3"}),
        )
    ```

=== "GET /foo3: request"

    ```json
    {
        "httpMethod": "GET",
        "path": "/foo3"
    }
    ```

=== "GET /foo3: response"

    ```json
    {
        "body": "{\"message\": \"Foo3\"}",
        "headers": {
            "Content-Type": "application/json",
            "custom-header": "value"
        },
        "isBase64Encoded": false,
        "statusCode": 200
    }
    ```
