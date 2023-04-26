from aws_lambda_powertools.utilities.data_classes import (
    CodePipelineJobEvent,
    event_source,
)


@event_source(data_class=CodePipelineJobEvent)
def lambda_handler(event, context):
    print(event)
