"""Handler with conflicting route for testing on_conflict='last'."""

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/users", summary="Get users from conflict_last")
def get_users_last():
    """This conflicts with users_handler.py - used to test on_conflict='last'."""
    return {"source": "conflict_last"}
