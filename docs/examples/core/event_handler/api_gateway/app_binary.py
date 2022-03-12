import os
from pathlib import Path

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response

app = APIGatewayRestResolver()
logo_file: bytes = Path(os.getenv("LAMBDA_TASK_ROOT") + "/logo.svg").read_bytes()


@app.get("/logo")
def get_logo():
    return Response(status_code=200, content_type="image/svg+xml", body=logo_file)


def lambda_handler(event, context):
    return app.resolve(event, context)
