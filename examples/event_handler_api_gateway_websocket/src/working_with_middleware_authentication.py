from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayWebSocketResolver()

sessions: dict[str, str] = {}  # (1)!


def validate_token(token: str | None) -> str | None:
    return "alice" if token == "Bearer valid-token" else None


def authenticate(app, next_middleware):
    user = validate_token(app.current_event.headers.get("Authorization"))  # (2)!
    if user is None:
        return None, 401  # (3)!
    sessions[app.current_event.request_context.connection_id] = user
    return next_middleware(app)


def inject_user(app, next_middleware):
    user = sessions.get(app.current_event.request_context.connection_id)
    if user is None:
        return {"error": "unauthenticated"}, 401
    app.append_context(user=user)  # (4)!
    return next_middleware(app)


@app.on_connect(middlewares=[authenticate])
def connect():
    return None


@app.on_disconnect()
def disconnect():
    sessions.pop(app.current_event.request_context.connection_id, None)


@app.route("orderUpdate", middlewares=[inject_user])
def order_update():
    order = app.current_event.json_body
    return {"orderId": order["orderId"], "status": "received", "processedFor": app.context["user"]}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
