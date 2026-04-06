"""Shared resolver - routes are registered by other files that import this."""

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()
