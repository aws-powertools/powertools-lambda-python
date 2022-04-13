from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils

tracer = Tracer(service="sample_graphql_transformer_resolver")
logger = Logger(service="sample_graphql_transformer_resolver")
app = AppSyncResolver()


@app.resolver(type_name="Query", field_name="listLocations")
def list_locations(page: int = 0, size: int = 10):
    return [{"id": 100, "name": "Smooth Grooves"}]


@app.resolver(field_name="commonField")
def common_field():
    # Would match all fieldNames matching 'commonField'
    return scalar_types_utils.make_id()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def lambda_handler(event, context):
    app.resolve(event, context)
