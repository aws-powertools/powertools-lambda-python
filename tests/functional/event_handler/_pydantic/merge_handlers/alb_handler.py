"""Sample ALB resolver handler for testing."""

from aws_lambda_powertools.event_handler import ALBResolver

app = ALBResolver()


@app.get("/alb/health")
def health_check():
    """ALB health check endpoint."""
    return {"status": "healthy", "resolver": "alb"}


@app.post("/alb/process")
def process_data():
    """ALB process endpoint."""
    return {"processed": True}
