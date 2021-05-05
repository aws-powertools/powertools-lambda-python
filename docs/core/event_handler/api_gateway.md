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
	  Api:
	    TracingEnabled: true
        Cors:								# see CORS section
          AllowOrigin: "'https://example.com'"
          AllowHeaders: "'Content-Type,Authorization,X-Amz-Date'"
          MaxAge: "'300'"
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
			    Path: /hello/{name}      # see Dynamic routes section
			    Method: GET
			CustomMessage:
			  Type: Api
			  Properties:
			    Path: /{message}/{name}  # see Dynamic routes section
			    Method: GET

	Outputs:
      HelloWorldApigwURL:
        Description: "API Gateway endpoint URL for Prod environment for Hello World Function"
        Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello"

    HelloWorldFunction:
        Description: "Hello World Lambda Function ARN"
        Value: !GetAtt HelloWorldFunction.Arn
	```

### API Gateway decorator

You can define your functions to match a path and HTTP method, when you use the decorator `ApiGatewayResolver`.

Here's an example where we have two separate functions to resolve two paths: `/hello`.

!!! info "We automatically serialize `Dict` responses as JSON and set content-type to `application/json`"

=== "app.py"

	```python hl_lines="3 7 9 12 18"
	from aws_lambda_powertools import Logger, Tracer
	from aws_lambda_powertools.logging import correlation_paths
	from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

	tracer = Tracer()
	logger = Logger()
	app = ApiGatewayResolver()  # by default API Gateway REST API (v1)

	@app.get("/hello")
	@tracer.capture_method
	def get_hello_universe():
		return {"message": "hello universe"}

	# You can continue to use other utilities just as before
	@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
	@tracer.capture_lambda_handler
	def lambda_handler(event, context):
		return app.resolve(event, context)
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

#### HTTP API

When using API Gateway HTTP API to front your Lambda functions, you can instruct `ApiGatewayResolver` to conform with their contract via `proxy_type` param:

=== "app.py"

	```python hl_lines="3 7"
	from aws_lambda_powertools import Logger, Tracer
	from aws_lambda_powertools.logging import correlation_paths
	from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType

	tracer = Tracer()
	logger = Logger()
	app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v2)

	@app.get("/hello")
	@tracer.capture_method
	def get_hello_universe():
		return {"message": "hello universe"}

	# You can continue to use other utilities just as before
	@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
	@tracer.capture_lambda_handler
	def lambda_handler(event, context):
		return app.resolve(event, context)
	```

#### ALB

When using ALB to front your Lambda functions, you can instruct `ApiGatewayResolver` to conform with their contract via `proxy_type` param:

=== "app.py"

	```python hl_lines="3 7"
	from aws_lambda_powertools import Logger, Tracer
	from aws_lambda_powertools.logging import correlation_paths
	from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType

	tracer = Tracer()
	logger = Logger()
	app = ApiGatewayResolver(proxy_type=ProxyEventType.alb_event)

	@app.get("/hello")
	@tracer.capture_method
	def get_hello_universe():
		return {"message": "hello universe"}

	# You can continue to use other utilities just as before
	@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPLICATION_LOAD_BALANCER)
	@tracer.capture_lambda_handler
	def lambda_handler(event, context):
		return app.resolve(event, context)
	```

### Dynamic routes

You can use `/path/{dynamic_value}` when configuring dynamic URL paths. This allows you to define such dynamic value as part of your function signature.

=== "app.py"

	```python hl_lines="9 11"
	from aws_lambda_powertools import Logger, Tracer
	from aws_lambda_powertools.logging import correlation_paths
	from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

	tracer = Tracer()
	logger = Logger()
	app = ApiGatewayResolver()

	@app.get("/hello/<name>")
	@tracer.capture_method
	def get_hello_you(name):
		return {"message": f"hello {name}}"}

	# You can continue to use other utilities just as before
	@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
	@tracer.capture_lambda_handler
	def lambda_handler(event, context):
		return app.resolve(event, context)
	```

You can also nest paths as configured earlier in [our sample infrastructure](#required-resources): `/{message}/{name}`.

=== "app.py"

	```python hl_lines="9 11"
	from aws_lambda_powertools import Logger, Tracer
	from aws_lambda_powertools.logging import correlation_paths
	from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

	tracer = Tracer()
	logger = Logger()
	app = ApiGatewayResolver()

	@app.get("/<message>/<name>")
	@tracer.capture_method
	def get_message(message, name):
		return {"message": f"{message}, {name}}"}

	# You can continue to use other utilities just as before
	@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
	@tracer.capture_lambda_handler
	def lambda_handler(event, context):
		return app.resolve(event, context)
	```

### CORS

You can configure CORS at the `ApiGatewayResolver` constructor via `cors` parameter using the `CORSConfig` class.

This will ensure that CORS headers are always returned as part of the response when your functions match the path invoked.

=== "app.py"

	```python hl_lines="9 11"
	from aws_lambda_powertools import Logger, Tracer
	from aws_lambda_powertools.logging import correlation_paths
	from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, CORSConfig

	tracer = Tracer()
	logger = Logger()

	cors_config = CORSConfig(allow_origin="https://example.com", max_age=300)
	app = ApiGatewayResolver(cors=cors_config)

	@app.get("/hello/<name>")
	@tracer.capture_method
	def get_hello_you(name):
		return {"message": f"hello {name}}"}

	@app.get("/hello", cors=False)  # optionally exclude CORS from response, if needed
	@tracer.capture_method
	def get_hello_no_cors_needed():
		return {"message": "hello, no CORS needed for this path ;)"}

	# You can continue to use other utilities just as before
	@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
	@tracer.capture_lambda_handler
	def lambda_handler(event, context):
		return app.resolve(event, context)
	```

!!! tip "Optionally disable class on a per path basis with `cors=False` parameter"

#### Defaults

For convenience, these are the default values when using `CORSConfig` to enable CORS:

!!! warning "Always configure `allow_origin` when using in production"

Key | Value | Note
------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------
**[allow_origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin){target="_blank"}**: `str` | `*` | Only use the default value for development. **Never use `*` for production** unless your use case requires it
**[allow_headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers){target="_blank"}**: `List[str]` | `[Authorization, Content-Type, X-Amz-Date, X-Api-Key, X-Amz-Security-Token]` | Additional headers will be appended to the default list for your convenience
**[expose_headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Expose-Headers){target="_blank"}**: `List[str]` | `[]` | Any additional header beyond the [safe listed by CORS specification](https://developer.mozilla.org/en-US/docs/Glossary/CORS-safelisted_response_header){target="_blank"}.
**[max_age](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Max-Age){target="_blank"}**: `int` | `` | Only for pre-flight requests if you choose to have your function to handle it instead of API Gateway
**[allow_credentials](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials){target="_blank"}**: `bool` | `False` | Only necessary when you need to expose cookies, authorization headers or TLS client certificates.

#### Pre-flight

Pre-flight (OPTIONS) calls are typically handled at the API Gateway level as per [our sample infrastructure](#required-resources), no Lambda integration necessary. However, ALB expects you to handle pre-flight requests.

For convenience, we automatically handle that for you as long as you [setup CORS in the constructor level](#cors).

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
    proxy_type=ProxyEventType.APIGatewayProxyEvent,
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
    post_data: dict = app.current_event.json_body
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
