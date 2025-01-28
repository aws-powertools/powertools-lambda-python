from aws_cdk import (
    Stack,
)
from aws_cdk.aws_lambda import Runtime
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct


class AgentsCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        action_group_function = PythonFunction(
            self,
            "LambdaFunction",
            runtime=Runtime.PYTHON_3_12,
            entry="./lambda",  # (1)!
            index="app.py",
            handler="lambda_handler",
        )

        agent = bedrock.Agent(
            self,
            "Agent",
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_INSTANT_V1_2,
            instruction="You are a helpful and friendly agent that answers questions about insurance claims.",
        )

        action_group: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="InsureClaimsSupport",
            description="Use these functions for insurance claims support",
            executor=bedrock.ActionGroupExecutor.fromlambda_function(
                lambda_function=action_group_function,
            ),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("./lambda/openapi.json"),  # (2)!
        )
        agent.add_action_group(action_group)
