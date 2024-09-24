from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CodeDeployLifecycleHookEvent(DictWrapper):
    @property
    def deployment_id(self) -> str:
        """The unique ID of the calling CodeDeploy Deployment."""
        return self["DeploymentId"]

    @property
    def lifecycle_event_hook_execution_id(self) -> str:
        """The unique ID of a deployments lifecycle hook."""
        return self["LifecycleEventHookExecutionId"]
