"""Sample REST API resolver handler for testing."""

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/rest/users")
def list_users():
    """List users via REST API."""
    return {"users": []}


@app.post("/rest/users")
def create_user():
    """Create user via REST API."""
    return {"created": True}
