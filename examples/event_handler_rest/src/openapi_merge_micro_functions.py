"""
Example: OpenAPI Merge for Micro Functions

This example demonstrates how to use configure_openapi_merge to generate
a unified OpenAPI schema from multiple Lambda handlers in a micro-function architecture.

Project structure:
    functions/
    ├── users/
    │   └── handler.py      # Users Lambda
    ├── orders/
    │   └── handler.py      # Orders Lambda
    └── products/
        └── handler.py      # Products Lambda
    openapi_lambda/
        └── handler.py      # OpenAPI Lambda (this file)
"""

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()

# Configure OpenAPI merge to discover and merge schemas from multiple Lambda handlers
app.configure_openapi_merge(
    path="./functions",  # Root directory containing Lambda handlers
    pattern="**/handler.py",  # Glob pattern to find handler files
    exclude=["**/tests/**", "**/__pycache__/**"],  # Patterns to exclude
    resolver_name="app",  # Name of the resolver variable in handler files
    title="My Unified API",
    version="1.0.0",
    description="Unified API documentation for all micro-functions",
    on_conflict="warn",  # Options: "warn", "error", "first", "last"
)

# Enable Swagger UI - it will automatically use the merged schema
app.enable_swagger(path="/swagger")


@app.get("/health")
def health_check():
    """Health check endpoint for the OpenAPI Lambda itself."""
    return {"status": "healthy"}


def handler(event, context):
    return app.resolve(event, context)
