from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.event_handler.request import Request
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()


# Middleware handles auth — it can return HTTP responses (redirects, 401s)
def auth_middleware(app, next_middleware):
    token = app.current_event.headers.get("authorization", "")
    if not token:
        return Response(status_code=401, body="Unauthorized")

    # Middleware writes to app.context
    app.append_context(user={"id": "user-123", "role": "admin"})
    return next_middleware(app)


app.use(middlewares=[auth_middleware])


# Depends() reads what middleware wrote via request.context — typed and testable
def get_current_user(request: Request) -> dict:
    return request.context["user"]


@app.get("/admin/dashboard")
def admin_dashboard(user: Annotated[dict, Depends(get_current_user)]):
    return {"message": f"Welcome {user['id']}", "role": user["role"]}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
