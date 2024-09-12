from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext

app = APIGatewayRestResolver()


@app.get("/ping")
def ping():
    return {"message": "pong"}  # (1)!


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
