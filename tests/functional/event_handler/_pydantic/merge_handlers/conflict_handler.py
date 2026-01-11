"""Handler with conflicting route (same as users_handler)."""

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/users")
def get_users_conflict():
    """This conflicts with users_handler.py."""
    return {"conflict": True}


def handler(event, context):
    return app.resolve(event, context)
