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
from aws_lambda_powertools.event_handler.bedrock_agent import BedrockAgentResolver, BedrockResponse
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
    "BedrockResponse",
    "CORSConfig",
    "LambdaFunctionUrlResolver",
    "Response",
    "VPCLatticeResolver",
    "VPCLatticeV2Resolver",
]
