"""
Example demonstrating File parameter usage in AWS Lambda Powertools Python Event Handler.

This example shows how to use the File parameter for handling multipart/form-data file uploads
with OpenAPI validation and automatic schema generation.
"""

from typing import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form


# Initialize resolver with OpenAPI validation enabled
app = APIGatewayRestResolver(enable_validation=True)


@app.post("/upload")
def upload_single_file(file: Annotated[bytes, File(description="File to upload")]):
    """Upload a single file."""
    return {"status": "uploaded", "file_size": len(file), "message": "File uploaded successfully"}


@app.post("/upload-with-metadata")
def upload_file_with_metadata(
    file: Annotated[bytes, File(description="File to upload")],
    description: Annotated[str, Form(description="File description")],
    tags: Annotated[str | None, Form(description="Optional tags")] = None,
):
    """Upload a file with additional form metadata."""
    return {
        "status": "uploaded",
        "file_size": len(file),
        "description": description,
        "tags": tags,
        "message": "File and metadata uploaded successfully",
    }


@app.post("/upload-multiple")
def upload_multiple_files(
    primary_file: Annotated[bytes, File(alias="primary", description="Primary file")],
    secondary_file: Annotated[bytes, File(alias="secondary", description="Secondary file")],
):
    """Upload multiple files."""
    return {
        "status": "uploaded",
        "primary_size": len(primary_file),
        "secondary_size": len(secondary_file),
        "total_size": len(primary_file) + len(secondary_file),
        "message": "Multiple files uploaded successfully",
    }


@app.post("/upload-with-constraints")
def upload_small_file(file: Annotated[bytes, File(description="Small file only", max_length=1024)]):
    """Upload a file with size constraints (max 1KB)."""
    return {
        "status": "uploaded",
        "file_size": len(file),
        "message": f"Small file uploaded successfully ({len(file)} bytes)",
    }


@app.post("/upload-optional")
def upload_optional_file(
    message: Annotated[str, Form(description="Required message")],
    file: Annotated[bytes | None, File(description="Optional file")] = None,
):
    """Upload with an optional file parameter."""
    return {
        "status": "processed",
        "message": message,
        "has_file": file is not None,
        "file_size": len(file) if file else 0,
    }


# Lambda handler function
def lambda_handler(event, context):
    """AWS Lambda handler function."""
    return app.resolve(event, context)


# The File parameter provides:
# 1. Automatic multipart/form-data parsing
# 2. OpenAPI schema generation with proper file upload documentation
# 3. Request validation with meaningful error messages
# 4. Support for file constraints (max_length, etc.)
# 5. Compatibility with WebKit and other browser boundary formats
# 6. Base64-encoded request handling (common in AWS Lambda)
# 7. Mixed file and form data support
# 8. Multiple file upload support
# 9. Optional file parameters
