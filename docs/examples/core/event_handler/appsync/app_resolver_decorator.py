from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils

tracer = Tracer(service="sample_resolver")
logger = Logger(service="sample_resolver")
app = AppSyncResolver()

# Note that `creation_time` isn't available in the schema
# This utility also takes into account what info you make available at API level vs what's stored
TODOS = [
    {
        "id": scalar_types_utils.make_id(),  # type ID or String
        "title": "First task",
        "description": "String",
        "done": False,
        "creation_time": scalar_types_utils.aws_datetime(),  # type AWSDateTime
    },
    {
        "id": scalar_types_utils.make_id(),
        "title": "Second task",
        "description": "String",
        "done": True,
        "creation_time": scalar_types_utils.aws_datetime(),
    },
]


@app.resolver(type_name="Query", field_name="getTodo")
def get_todo(id: str = ""):
    logger.info(f"Fetching Todo {id}")
    todo = [todo for todo in TODOS if todo["id"] == id]

    return todo


@app.resolver(type_name="Query", field_name="listTodos")
def list_todos():
    return TODOS


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
