import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

app = APIGatewayRestResolver()
logger = Logger()


def inject_correlation_id(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
    request_id = app.current_event.request_context.request_id  # (1)!

    # Use API Gateway REST API request ID if caller didn't include a correlation ID
    correlation_id = logger.get_correlation_id() or request_id  # (2)!

    # Inject correlation ID in shared context and Logger
    app.append_context(correlation_id=correlation_id)  # (3)!
    logger.set_correlation_id(correlation_id)

    # Get response from next middleware OR /todos route
    result = next_middleware(app)  # (4)!

    # Include Correlation ID in the response back to caller
    result.headers["x-correlation-id"] = correlation_id  # (5)!
    return result


@app.get("/todos", middlewares=[inject_correlation_id])  # (6)!
def get_todos():
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@logger.inject_lambda_context(correlation_id_path='headers."x-correlation-id"')  # (7)!
def lambda_handler(event, context):
    return app.resolve(event, context)
