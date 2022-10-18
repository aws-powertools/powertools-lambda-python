from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
    content_types,
)

app = APIGatewayHttpResolver()

# The reason we use post is that whoever is writing tests can easily assert on the
# content being sent (body, headers, cookies, content-type) to reduce cognitive load.


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


def lambda_handler(event, context):
    return app.resolve(event, context)
