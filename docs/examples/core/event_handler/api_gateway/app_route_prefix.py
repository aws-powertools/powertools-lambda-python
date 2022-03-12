from typing import Dict

import users

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver()
app.include_router(users.router, prefix="/users")  # prefix '/users' to any route in `users.router`


def lambda_handler(event: Dict, context: LambdaContext):
    return app.resolve(event, context)
