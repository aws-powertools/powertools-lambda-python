from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/upload")
def upload_file(
    file_data: Annotated[bytes, File(description="File to upload")],  # (1)!
):
    return {"file_size": len(file_data)}


def lambda_handler(event, context):
    return app.resolve(event, context)
