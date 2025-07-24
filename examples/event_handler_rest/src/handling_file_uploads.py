from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form

app = APIGatewayRestResolver(enable_validation=True)


@app.post("/upload")
def upload_file(
    file: Annotated[bytes, File(description="File to upload")],
    filename: Annotated[str, Form(description="Name of the file")]
):
    # file contains the binary data of the uploaded file
    # filename contains the form field value
    return {
        "message": f"Uploaded {filename}",
        "size": len(file)
    }


def lambda_handler(event, context):
    return app.resolve(event, context)
