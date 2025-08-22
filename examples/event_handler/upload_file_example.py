"""
Example of using UploadFile with OpenAPI schema generation

This example demonstrates how to use the UploadFile class with FastAPI-like
file handling and proper OpenAPI schema generation.
"""

from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form, UploadFile

app = APIGatewayRestResolver()


@app.post("/upload")
def upload_file(file: Annotated[UploadFile, File()]):
    """
    Upload a single file.

    Returns file metadata and a preview of the content.
    """
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "content_preview": file.file[:100].decode() if file.size < 10000 else "Content too large to preview",
    }


@app.post("/upload-multiple")
def upload_multiple_files(
    primary_file: Annotated[UploadFile, File(alias="primary", description="Primary file with metadata")],
    secondary_file: Annotated[bytes, File(alias="secondary", description="Secondary file as bytes")],
    description: Annotated[str, Form(description="Description of the uploaded files")],
):
    """
    Upload multiple files with form data.

    Shows how to mix UploadFile, bytes files, and form data in the same endpoint.
    """
    return {
        "status": "uploaded",
        "description": description,
        "primary_filename": primary_file.filename,
        "primary_content_type": primary_file.content_type,
        "primary_size": primary_file.size,
        "secondary_size": len(secondary_file),
        "total_size": primary_file.size + len(secondary_file),
    }


@app.post("/upload-with-headers")
def upload_with_headers(file: Annotated[UploadFile, File()]):
    """
    Upload a file and access its headers.

    Demonstrates how to access all headers from the multipart section.
    """
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "headers": file.headers,
    }


def handler(event, context):
    return app.resolve(event, context)


if __name__ == "__main__":
    # Print the OpenAPI schema for testing
    schema = app.get_openapi_schema(title="File Upload API", version="1.0.0")
    print("\n✅ OpenAPI schema generated successfully!")
