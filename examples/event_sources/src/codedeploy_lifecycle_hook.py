from aws_lambda_powertools.utilities.data_classes import CodeDeployLifecycleHookEvent, event_source


@event_source(data_class=CodeDeployLifecycleHookEvent)
def lambda_handler(event: CodeDeployLifecycleHookEvent, context):
    deployment_id = event.deployment_id
    lifecycle_event_hook_execution_id = event.lifecycle_event_hook_execution_id

    return {"deployment_id": deployment_id, "lifecycle_event_hook_execution_id": lifecycle_event_hook_execution_id}
