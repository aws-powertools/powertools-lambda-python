from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event, context: LambdaContext):
    # Retrieve multiple secrets in a single API call
    secrets = parameters.get_secrets_by_name(
        [
            "database/password",
            "api/key",
            "jwt/secret",
        ],
    )

    # Access individual secrets
    db_password = secrets["database/password"]
    api_key = secrets["api/key"]
    jwt_secret = secrets["jwt/secret"]

    do_stuff_with_secrets(db_password, api_key, jwt_secret)

    # Use secrets in your application logic
    return {
        "statusCode": 200,
        "body": f"Retrieved {len(secrets)} secrets successfully",
    }


def do_stuff_with_secrets(db_password, api_key, jwt_secret):
    pass
