"""
Event handler decorators for common Lambda events
"""

from aws_lambda_powertools.event_handler.api_gateway import (
    ALBResolver,
    APIGatewayHttpResolver,
    ApiGatewayResolver,
    APIGatewayRestResolver,
    CORSConfig,
    Response,
)
from aws_lambda_powertools.event_handler.appsync import AppSyncResolver
from aws_lambda_powertools.event_handler.bedrock_agent import BedrockAgentResolver
from aws_lambda_powertools.event_handler.bedrock_agent_function import BedrockAgentFunctionResolver, BedrockResponse
from aws_lambda_powertools.event_handler.events_appsync.appsync_events import AppSyncEventsResolver
from aws_lambda_powertools.event_handler.lambda_function_url import (
    LambdaFunctionUrlResolver,
)
from aws_lambda_powertools.event_handler.vpc_lattice import VPCLatticeResolver, VPCLatticeV2Resolver

__all__ = [
    "AppSyncResolver",
    "AppSyncEventsResolver",
    "APIGatewayRestResolver",
    "APIGatewayHttpResolver",
    "ALBResolver",
    "ApiGatewayResolver",
    "BedrockAgentResolver",
    "BedrockAgentFunctionResolver",
    "CORSConfig",
    "LambdaFunctionUrlResolver",
    "Response",
    "BedrockResponse",
    "VPCLatticeResolver",
    "VPCLatticeV2Resolver",
]
