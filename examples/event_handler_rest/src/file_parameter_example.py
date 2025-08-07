"""
Example demonstrating File parameter usage for handling file uploads.
This showcases both the new UploadFile class for metadata access and
backward-compatible bytes approach.
"""

from __future__ import annotations

from typing import Annotated, Union

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form, UploadFile

# Initialize resolver with OpenAPI validation enabled
app = APIGatewayRestResolver(enable_validation=True)


# ========================================
# NEW: UploadFile with Metadata Access
# ========================================


@app.post("/upload-with-metadata")
def upload_file_with_metadata(file: Annotated[UploadFile, File(description="File with metadata access")]):
    """Upload a file with full metadata access - NEW UploadFile feature!"""
    return {
        "status": "uploaded",
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size": file.size,
        "headers": file.headers,
        "content_preview": file.read(100).decode("utf-8", errors="ignore"),
        "can_reconstruct_file": True,
        "message": "File uploaded with metadata access",
    }


@app.post("/upload-mixed-form")
def upload_file_with_form_data(
    file: Annotated[UploadFile, File(description="File with metadata")],
    description: Annotated[str, Form(description="File description")],
    category: Annotated[str | None, Form(description="File category")] = None,
):
    """Upload file with UploadFile metadata + form data."""
    return {
        "status": "uploaded",
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size": file.size,
        "description": description,
        "category": category,
        "custom_headers": {k: v for k, v in file.headers.items() if k.startswith("X-")},
        "message": "File and form data uploaded with metadata",
    }


# ========================================
# BACKWARD COMPATIBLE: Bytes Approach
# ========================================


@app.post("/upload")
def upload_single_file(file: Annotated[bytes, File(description="File to upload")]):
    """Upload a single file - LEGACY bytes approach (still works!)."""
    return {"status": "uploaded", "file_size": len(file), "message": "File uploaded successfully"}


@app.post("/upload-legacy-metadata")
def upload_file_legacy_with_metadata(
    file: Annotated[bytes, File(description="File to upload")],
    description: Annotated[str, Form(description="File description")],
    tags: Annotated[Union[str, None], Form(description="Optional tags")] = None,  # noqa: UP007
):
    """Upload a file with additional form metadata - LEGACY bytes approach."""
    return {
        "status": "uploaded",
        "file_size": len(file),
        "description": description,
        "tags": tags,
        "message": "File and metadata uploaded successfully",
    }


@app.post("/upload-multiple")
def upload_multiple_files(
    primary_file: Annotated[UploadFile, File(alias="primary", description="Primary file with metadata")],
    secondary_file: Annotated[bytes, File(alias="secondary", description="Secondary file as bytes")],
):
    """Upload multiple files - showcasing BOTH UploadFile and bytes approaches."""
    return {
        "status": "uploaded",
        "primary_filename": primary_file.filename,
        "primary_content_type": primary_file.content_type,
        "primary_size": primary_file.size,
        "secondary_size": len(secondary_file),
        "total_size": primary_file.size + len(secondary_file),
        "message": "Multiple files uploaded with mixed approaches",
    }


@app.post("/upload-with-constraints")
def upload_small_file(file: Annotated[bytes, File(description="Small file only", max_length=1024)]):
    """Upload a file with size constraints (max 1KB) - bytes approach."""
    return {
        "status": "uploaded",
        "file_size": len(file),
        "message": f"Small file uploaded successfully ({len(file)} bytes)",
    }


@app.post("/upload-optional")
def upload_optional_file(
    message: Annotated[str, Form(description="Required message")],
    file: Annotated[UploadFile | None, File(description="Optional file with metadata")] = None,
):
    """Upload with an optional UploadFile parameter - NEW approach!"""
    return {
        "status": "processed",
        "message": message,
        "has_file": file is not None,
        "filename": file.filename if file else None,
        "content_type": file.content_type if file else None,
        "file_size": file.size if file else 0,
    }


# Lambda handler function
def lambda_handler(event, context):
    """AWS Lambda handler function."""
    return app.resolve(event, context)


# The File parameter now provides TWO approaches:
#
# 1. NEW UploadFile Class (Recommended):
#    - filename property (e.g., "document.pdf")
#    - content_type property (e.g., "application/pdf")
#    - size property (file size in bytes)
#    - headers property (dict of all multipart headers)
#    - read() method (flexible content access)
#    - Perfect for file reconstruction in Lambda/S3 scenarios
#
# 2. LEGACY bytes approach (Backward Compatible):
#    - Direct bytes content access
#    - Existing code continues to work unchanged
#    - Automatic conversion from UploadFile to bytes when needed
#
# Both approaches provide:
# - Automatic multipart/form-data parsing
# - OpenAPI schema generation with proper file upload documentation
# - Request validation with meaningful error messages
# - Support for file constraints (max_length, etc.)
# - Compatibility with WebKit and other browser boundary formats
# - Base64-encoded request handling (common in AWS Lambda)
# - Mixed file and form data support
# - Multiple file upload support
# - Optional file parameters
