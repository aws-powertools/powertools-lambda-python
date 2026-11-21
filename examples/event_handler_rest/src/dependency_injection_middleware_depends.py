from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()


class UserDao:
    def get(self, sub: str) -> dict | None:
        # fetch user from a database
        ...


def get_user_dao() -> UserDao:
    return UserDao()


# Middleware can declare Depends() parameters, just like route handlers
def user_middleware(
    app: APIGatewayHttpResolver,
    next_middleware: NextMiddleware,
    user_dao: Annotated[UserDao, Depends(get_user_dao)],
):
    authorizer = app.current_event.request_context.authorizer
    if authorizer:
        sub: str | None = authorizer.jwt_claim.get("sub")
        if sub:
            user = user_dao.get(sub)
            if user:
                app.append_context(user=user)
    return next_middleware(app)


app.use(middlewares=[user_middleware])


@app.get("/profile")
def get_profile():
    return {"user": app.context.get("user")}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
