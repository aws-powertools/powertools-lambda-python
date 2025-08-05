from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get("/api/<api_version>/resources/<resource_type>/<resource_id>")
@tracer.capture_method
def get_resource(api_version: str, resource_type: str, resource_id: str):
    # handles nested dynamic parameters in API versioned routes
    return {
        "version": api_version,
        "type": resource_type,
        "id": resource_id,
    }


@app.get("/organizations/<org_id>/teams/<team_id>/members")
@tracer.capture_method
def list_team_members(org_id: str, team_id: str):
    # combines dynamic paths with static segments
    return {"org": org_id, "team": team_id, "action": "list_members"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
