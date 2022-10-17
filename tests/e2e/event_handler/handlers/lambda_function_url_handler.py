from aws_lambda_powertools.event_handler import (
    LambdaFunctionUrlResolver,
    Response,
    content_types,
)

app = LambdaFunctionUrlResolver()


@app.post("/todos")
def todos():
    payload = app.current_event.json_body

    body = payload.get("body", "Hello World")
    status_code = payload.get("status_code", 200)
    headers = payload.get("headers", {})
    cookies = payload.get("cookies", [])
    content_type = headers.get("Content-Type", content_types.TEXT_PLAIN)

    return Response(
        status_code=status_code,
        content_type=content_type,
        body=body,
        cookies=cookies,
        headers=headers,
    )


@app.get("/hello")
def hello():
    return Response(status_code=200, content_type=content_types.TEXT_PLAIN, body="Hello World")


def lambda_handler(event, context):
    return app.resolve(event, context)
