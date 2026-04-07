from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

app = APIGatewayRestResolver()
logger = Logger()


def request_context_middleware(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
    request = app.request  # (1)!

    logger.append_keys(
        route=request.route,  # (2)!
        method=request.method,
        path_parameters=request.path_parameters,  # (3)!
    )

    response = next_middleware(app)

    response.headers["x-route-pattern"] = request.route  # (4)!
    return response


@app.get("/todos/<todo_id>", middlewares=[request_context_middleware])
def get_todo(todo_id: str):
    return {"id": todo_id}


def lambda_handler(event, context):
    return app.resolve(event, context)
