from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/hello", compress=True)
def get_hello_you():
    return {"message": "hello universe"}


def lambda_handler(event, context):
    return app.resolve(event, context)
