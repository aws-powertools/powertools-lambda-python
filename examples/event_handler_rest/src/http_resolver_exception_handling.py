from aws_lambda_powertools.event_handler import HttpResolverAlpha, Response

app = HttpResolverAlpha()


class NotFoundError(Exception):
    def __init__(self, resource: str):
        self.resource = resource


@app.exception_handler(NotFoundError)
def handle_not_found_error(exc: NotFoundError):
    return Response(
        status_code=404,
        content_type="application/json",
        body={"error": "Not Found", "resource": exc.resource},
    )


@app.not_found
def handle_not_found(exc: Exception):
    return Response(
        status_code=404,
        content_type="application/json",
        body={"error": "Route not found", "path": app.current_event.path},
    )


@app.get("/users/<user_id>")
def get_user(user_id: str):
    if user_id == "0":
        raise NotFoundError(f"User {user_id}")
    return {"user_id": user_id}


handler = app
