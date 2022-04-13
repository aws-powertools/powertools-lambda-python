from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import CodePipelineJobEvent, event_source

logger = Logger()


@event_source(data_class=CodePipelineJobEvent)
def lambda_handler(event, context):
    """The Lambda function handler

    If a continuing job then checks the CloudFormation stack status
    and updates the job accordingly.

    If a new job then kick of an update or creation of the target
    CloudFormation stack.
    """

    # Extract the Job ID
    job_id = event.get_id

    # Extract the params
    params: dict = event.decoded_user_parameters
    stack = params["stack"]
    artifact_name = params["artifact"]
    template_file = params["file"]

    try:
        if event.data.continuation_token:
            # If we're continuing then the create/update has already been triggered
            # we just need to check if it has finished.
            check_stack_update_status(job_id, stack)
        else:
            template = event.get_artifact(artifact_name, template_file)
            # Kick off a stack update or create
            start_update_or_create(job_id, stack, template)
    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail the job and log the exception message.
        logger.exception("Function failed due to exception.")
        put_job_failure(job_id, "Function exception: " + str(e))

    logger.debug("Function complete.")
    return "Complete."
