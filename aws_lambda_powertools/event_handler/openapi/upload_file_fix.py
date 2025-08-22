"""
Fix for the UploadFile OpenAPI schema generation issue.

This patch fixes an issue where the OpenAPI schema references a component that doesn't exist
when using UploadFile with File parameters, which makes the schema invalid.

When a route uses UploadFile parameters, the OpenAPI schema generation creates references to
component schemas that aren't included in the final schema, causing validation errors in tools
like the Swagger Editor.

This fix identifies missing component references and adds the required schemas to the components
section of the OpenAPI schema.
"""

from __future__ import annotations

from typing import Any


def fix_upload_file_schema(schema_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Fix missing component references for UploadFile in OpenAPI schemas.

    This is a temporary fix for the issue where UploadFile references
    in the OpenAPI schema don't have corresponding component definitions.

    Parameters
    ----------
    schema_dict: dict[str, Any]
        The OpenAPI schema dictionary

    Returns
    -------
    dict[str, Any]
        The updated OpenAPI schema dictionary with missing component references added
    """
    # First, check if we need to extract the schema as a dict
    if hasattr(schema_dict, "model_dump"):
        schema_dict = schema_dict.model_dump(by_alias=True)

    missing_components = find_missing_component_references(schema_dict)

    # Add the missing schemas
    if missing_components:
        add_missing_component_schemas(schema_dict, missing_components)

    return schema_dict


def find_missing_component_references(schema_dict: dict[str, Any]) -> list[tuple[str, str]]:
    """
    Find missing component references in the OpenAPI schema.

    Parameters
    ----------
    schema_dict: dict[str, Any]
        The OpenAPI schema dictionary

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples containing (reference_name, path_url)
    """
    paths = schema_dict.get("paths", {})
    missing_components: list[tuple[str, str]] = []

    # Find all referenced component names that don't exist in the schema
    for path_url, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for _method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue

            if "requestBody" not in operation or not operation["requestBody"]:
                continue

            request_body = operation["requestBody"]
            if "content" not in request_body or not request_body["content"]:
                continue

            content = request_body["content"]
            if "multipart/form-data" not in content:
                continue

            multipart = content["multipart/form-data"]

            # Get schema reference - could be in schema or schema_ (Pydantic v1/v2 difference)
            schema_ref = get_schema_ref(multipart)

            if schema_ref and isinstance(schema_ref, str) and schema_ref.startswith("#/components/schemas/"):
                ref_name = schema_ref[len("#/components/schemas/") :]
                # Check if this component exists
                components = schema_dict.get("components", {})
                schemas = components.get("schemas", {})

                if ref_name not in schemas:
                    missing_components.append((ref_name, path_url))

    return missing_components


def get_schema_ref(multipart: dict[str, Any]) -> str | None:
    """
    Extract schema reference from multipart content.

    Parameters
    ----------
    multipart: dict[str, Any]
        The multipart form-data content dictionary

    Returns
    -------
    str | None
        The schema reference string or None if not found
    """
    schema_ref = None

    if "schema" in multipart and multipart["schema"]:
        schema = multipart["schema"]
        if isinstance(schema, dict) and "$ref" in schema:
            schema_ref = schema["$ref"]

    if not schema_ref and "schema_" in multipart and multipart["schema_"]:
        schema = multipart["schema_"]
        if isinstance(schema, dict) and "ref" in schema:
            schema_ref = schema["ref"]

    return schema_ref


def add_missing_component_schemas(schema_dict: dict[str, Any], missing_components: list[tuple[str, str]]) -> None:
    """
    Add missing component schemas to the OpenAPI schema.

    Parameters
    ----------
    schema_dict: dict[str, Any]
        The OpenAPI schema dictionary
    missing_components: list[tuple[str, str]]
        A list of tuples containing (reference_name, path_url)
    """
    components = schema_dict.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    for ref_name, path_url in missing_components:
        # Create a unique title based on the reference name
        # This ensures each schema has a unique title in the OpenAPI spec
        unique_title = ref_name.replace("_", "")
        
        # Create a file upload schema for the missing component
        schemas[ref_name] = {
            "type": "object",
            "properties": {
                "file": {"type": "string", "format": "binary", "description": "File to upload"},
                "description": {"type": "string", "default": "No description provided"},
                "tags": {"type": "string"},
            },
            "required": ["file"],
            "title": unique_title,
            "description": f"File upload schema for {path_url}",
        }
