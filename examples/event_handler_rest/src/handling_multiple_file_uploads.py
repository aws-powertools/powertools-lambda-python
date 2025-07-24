from typing import Annotated, List

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/upload-multiple")
def upload_multiple_files(
    files: Annotated[List[bytes], File(description="Files to upload")],
    description: Annotated[str, Form(description="Upload description")]
):
    return {
        "message": f"Uploaded {len(files)} files",
        "description": description,
        "total_size": sum(len(file) for file in files)
    }


def lambda_handler(event, context):
    return app.resolve(event, context)
