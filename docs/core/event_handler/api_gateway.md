---
title: API Gateway
description: Core utility
---

Event handler for AWS API Gateway and Application Loader Balancers.

### Key Features

* Routes - `@app.get("/foo")`
* Path expressions - `@app.delete("/delete/<uid>")`
* Cors - `@app.post("/make_foo", cors=True)` or via `CORSConfig` and builtin CORS preflight route
* Base64 encode binary - `@app.get("/logo.png")`
* Gzip Compression - `@app.get("/large-json", compression=True)`
* Cache-control - `@app.get("/foo", cache_control="max-age=600")`
* Rest API simplification with function returns a Dict
* Support function returns a Response object which give fine-grained control of the headers
* JSON encoding of Decimals


### All in one example

> TODO - Break on into smaller examples

=== "app.py"

```python
from decimal import Decimal
import json
from typing import Dict, Tuple

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    CORSConfig,
    ProxyEventType,
    Response,
)

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
```
