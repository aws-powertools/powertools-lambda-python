from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get(".+")
@tracer.capture_method
def catch_any_route_get_method():
    return {"path_received": app.current_event.path}


# File path proxy - captures everything after /files/
@app.get("/files/.+")
def serve_file():
    file_path = app.current_event.path.replace("/files/", "")
    return {"file_path": file_path}


# API versioning with any format
@app.get(r"/api/v\d+/.*")  # Matches /api/v1/users, /api/v2/posts/123
def handle_versioned_api():
    return {"api_version": "handled"}


# Catch-all for unmatched routes
@app.route(".*", method=["GET", "POST"])  # Must be last route
def catch_all():
    return {"message": "Route not found", "path": app.current_event.path}


# Mixed: dynamic parameter + regex catch-all
@app.get("/users/<user_id>/files/.+")
def get_user_files(user_id: str):
    file_path = app.current_event.path.split(f"/users/{user_id}/files/")[1]
    return {"user_id": user_id, "file_path": file_path}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
