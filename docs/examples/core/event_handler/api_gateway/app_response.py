import json

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response

app = APIGatewayRestResolver()


@app.get("/hello")
def get_hello_you():
    payload = json.dumps({"message": "I'm a teapot"})
    custom_headers = {"X-Custom": "X-Value"}

    return Response(
        status_code=418,
        content_type="application/json",
        body=payload,
        headers=custom_headers,
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
