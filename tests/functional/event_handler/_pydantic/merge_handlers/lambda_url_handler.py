"""Sample Lambda Function URL resolver handler for testing."""

from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver

app = LambdaFunctionUrlResolver()


@app.get("/lambda-url/status")
def get_status():
    """Get Lambda URL status."""
    return {"status": "ok", "resolver": "lambda_url"}


@app.post("/lambda-url/webhook")
def webhook():
    """Webhook endpoint."""
    return {"received": True}
