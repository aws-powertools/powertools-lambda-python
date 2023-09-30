from typing import Any

import requests

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def access_token(client_id: str, client_secret: str, audience: str) -> str:
    # example function that returns a JWT access token
    ...

    return access_token

def lambda_handler(event: dict, context: LambdaContext):

    try:
        # Usually an endpoint is not sensitive data, so we store it in SSM Parameters
        client_id: Any = parameters.get_parameter("/lambda-powertools/client_id")
        client_secret: Any = parameters.get_parameter("/lambda-powertools/client_secret")
        audience: Any = parameters.get_parameter("/lambda-powertools/audience")

        jwt_token = access_token(client_id=client_id, client_secret=client_secret, audience=audience)

        # set-secret will create a new secret if it doesn't exist and return the version id
        update_secret = parameters.set_secret(name="/lambda-powertools/api-key", value=jwt_token)

        return {"access_token": "updated", "statusCode": 200}
    except parameters.exceptions.GetParameterError as error:
        return {"access_token": "updated", "statusCode": 400}
