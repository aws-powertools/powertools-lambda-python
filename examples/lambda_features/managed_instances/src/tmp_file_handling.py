from pathlib import Path

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    # Use unique file names to avoid conflicts
    request_id = context.aws_request_id
    temp_file = Path(f"/tmp/data_{request_id}.json")

    try:
        with temp_file.open("w") as f:
            f.write('{"data": "example"}')

        # Process file...

    finally:
        # Clean up to avoid filling /tmp
        if temp_file.exists():
            temp_file.unlink()

    return {"statusCode": 200}
