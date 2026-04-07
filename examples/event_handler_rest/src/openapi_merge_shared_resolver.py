# Central resolver definition - shared_resolver.py
from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()
