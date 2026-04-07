"""Sample HTTP API resolver handler for testing."""

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver

app = APIGatewayHttpResolver()


@app.get("/http/items")
def list_items():
    """List items via HTTP API."""
    return {"items": []}


@app.get("/http/items/<item_id>")
def get_item(item_id: str):
    """Get item by ID."""
    return {"item_id": item_id}
