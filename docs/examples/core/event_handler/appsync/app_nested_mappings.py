from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer(service="sample_resolver")
logger = Logger(service="sample_resolver")
app = AppSyncResolver()


@app.resolver(field_name="listLocations")
@app.resolver(field_name="locations")
def get_locations(name: str, description: str = ""):
    return name + description


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
