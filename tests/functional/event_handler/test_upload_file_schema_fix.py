from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayRestResolver,
)
from aws_lambda_powertools.event_handler.openapi.params import UploadFile
from aws_lambda_powertools.event_handler.openapi.upload_file_fix import fix_upload_file_schema


class TestUploadFileSchemaFix:
    def test_upload_file_components_are_added(self):
        # GIVEN a schema with missing component references (simulating the issue)
        mock_schema = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "0.1.0"},
            "paths": {
                "/upload_with_metadata": {
                    "post": {
                        "summary": "Upload With Metadata",
                        "requestBody": {
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UploadFile_upload_with_metadata"
                                    }
                                }
                            },
                            "required": True,
                        },
                        "responses": {"200": {"description": "Successful Response"}},
                    }
                }
            },
            # Note: components section is missing, which is the problem our fix addresses
        }

        # WHEN we apply the fix
        fixed_schema = fix_upload_file_schema(mock_schema)

        # THEN the schema should have the correct components
        paths = fixed_schema.get("paths", {})
        assert "/upload_with_metadata" in paths

        # Check if POST operation exists
        post_op = paths["/upload_with_metadata"].get("post")
        assert post_op is not None

        # Check request body
        request_body = post_op.get("requestBody")
        assert request_body is not None

        # Check content
        content = request_body.get("content")
        assert content is not None
        assert "multipart/form-data" in content

        # Check schema reference
        multipart = content["multipart/form-data"]
        assert multipart is not None

        # Handle both schema and schema_ fields (Pydantic v1 vs v2 compatibility)
        schema = None
        if "schema" in multipart and multipart["schema"]:
            schema = multipart["schema"]
        elif "schema_" in multipart and multipart["schema_"]:
            schema = multipart["schema_"]

        assert schema is not None

        # Get the reference from either the direct field or nested schema_ field
        ref = None
        if "$ref" in schema:
            ref = schema["$ref"]
        elif "ref" in schema:
            ref = schema["ref"]

        assert ref is not None
        assert ref.startswith("#/components/schemas/")

        # Get referenced component name
        component_name = ref[len("#/components/schemas/") :]

        # Check if the component exists in the schemas
        components = fixed_schema.get("components", {})
        schemas = components.get("schemas", {})
        assert component_name in schemas, f"Component {component_name} is missing from schemas"

        # Verify the component has the correct structure
        component = schemas[component_name]
        assert component["type"] == "object"
        assert "properties" in component
        assert "file" in component["properties"]
        assert component["properties"]["file"]["type"] == "string"
        assert component["properties"]["file"]["format"] == "binary"
        assert "required" in component
        assert "file" in component["required"]
