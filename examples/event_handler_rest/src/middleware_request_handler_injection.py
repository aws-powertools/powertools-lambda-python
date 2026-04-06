from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request

app = APIGatewayRestResolver()


@app.get("/todos/<todo_id>")
def get_todo(todo_id: str, request: Request):  # (1)!
    return {
        "id": todo_id,
        "route": request.route,  # (2)!
        "user_agent": request.headers.get("user-agent", ""),
    }


def lambda_handler(event, context):
    return app.resolve(event, context)
