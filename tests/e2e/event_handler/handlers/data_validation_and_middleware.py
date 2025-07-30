from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.utilities.typing import LambdaContext


def middleware_auth(app: APIGatewayRestResolver, next_middleware: NextMiddleware):
    # Return early response
    return Response(status_code=202, content_type="application/json", body="{}")


app = APIGatewayRestResolver(enable_validation=True)
app.use(middlewares=[middleware_auth])


class MyModel(BaseModel):
    name: str


@app.get("/data_validation_middleware")
def get_data_validation_and_middleware() -> MyModel:
    return MyModel(name="powertools")


def lambda_handler(event, context: LambdaContext):
    return app.resolve(event, context)
