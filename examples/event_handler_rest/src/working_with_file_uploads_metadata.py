from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/upload")
def upload_file(
    file_data: Annotated[UploadFile, File(description="File to upload")],  # (1)!
):
    return {
        "filename": file_data.filename,  # (2)!
        "content_type": file_data.content_type,
        "file_size": len(file_data),
    }


def lambda_handler(event, context):
    return app.resolve(event, context)
