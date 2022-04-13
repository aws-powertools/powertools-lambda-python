from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver(debug=True)


@app.get("/hello")
def get_hello_universe():
    return {"message": "hello universe"}


def lambda_handler(event, context):
    return app.resolve(event, context)
