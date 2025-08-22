import json
import tempfile

from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile


class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle enum values."""

    def default(self, obj):
        """Convert enum to string."""
        if hasattr(obj, "value") and not callable(obj.value):
            return obj.value
        return super().default(obj)


class TestUploadFileOpenAPIValidator:
    """Test that OpenAPI schema for UploadFile is valid and has correct component references."""

    def test_uploadfile_openapi_schema_validation(self):  # noqa: PLR0915
        """Test if the OpenAPI schema generated with UploadFile can be validated."""
        # Create test app with upload endpoint
        app = APIGatewayRestResolver()

        @app.post("/upload-with-metadata")
        def upload_file_with_metadata(
            file: Annotated[UploadFile, File(description="File to upload")],
            description: str = "No description provided",
            tags: str = None,
        ):
            """Upload a file with additional metadata."""
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "description": description,
                "tags": tags or [],
            }

        # Generate OpenAPI schema
        schema = app.get_openapi_schema()
        schema_dict = schema.model_dump(by_alias=True)

        # Create a temporary file for manual inspection if needed
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
            json.dump(schema_dict, tmp, cls=EnumEncoder, indent=2)
            tmp_path = tmp.name

        # Access the schema paths
        paths = schema_dict.get("paths", {})

        # Assert that the path exists
        assert "/upload-with-metadata" in paths

        # Get the operation
        path_item = paths["/upload-with-metadata"]
        assert "post" in path_item

        # Get the request body
        operation = path_item["post"]
        assert "requestBody" in operation

        # Get the content
        req_body = operation["requestBody"]
        assert "content" in req_body

        # Get the multipart form data
        content = req_body["content"]
        assert "multipart/form-data" in content

        # Get the schema
        multipart = content["multipart/form-data"]
        assert "schema" in multipart

        # Check if schema is a reference
        schema_ref = multipart["schema"]
        if "$ref" in schema_ref:
            ref = schema_ref["$ref"]

            # Verify that the reference points to a component
            assert ref.startswith("#/components/schemas/")

            # Extract component name
            component_name = ref[len("#/components/schemas/") :]

            # Verify that the component exists
            components = schema_dict.get("components", {})
            schemas = components.get("schemas", {})

            # This is the key assertion that verifies the reference exists
            assert component_name in schemas, f"Component {component_name} not found in schema"

        # Check if the path exists in the schema
        assert "/upload-with-metadata" in schema_dict["paths"]
        upload_path = schema_dict["paths"]["/upload-with-metadata"]
        assert "post" in upload_path

        # Check if there's a requestBody with multipart/form-data
        assert "requestBody" in upload_path["post"]
        assert "content" in upload_path["post"]["requestBody"]
        assert "multipart/form-data" in upload_path["post"]["requestBody"]["content"]

        # Get the schema reference
        form_data = upload_path["post"]["requestBody"]["content"]["multipart/form-data"]
        assert "schema" in form_data

        # Check if it's a reference
        if "$ref" in form_data["schema"]:
            ref_path = form_data["schema"]["$ref"]
            print(f"\nSchema references: {ref_path}")

            # Extract the component name from the reference
            component_name = ref_path.split("/")[-1]

            # Check if the referenced component exists
            assert "components" in schema_dict
            assert "schemas" in schema_dict["components"]

            # This assertion should fail if the component doesn't exist
            assert component_name in schema_dict["components"]["schemas"], (
                f"Referenced component '{component_name}' not found in schemas"
            )

        # Write schema to a file for validation with external tools if needed
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
            json.dump(schema_dict, tmp, cls=EnumEncoder)
