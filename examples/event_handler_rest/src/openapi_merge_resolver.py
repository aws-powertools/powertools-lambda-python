from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()

# Configure merge - discovers handlers but doesn't execute them
app.configure_openapi_merge(
    path="./functions",
    pattern="**/handler.py",
    title="My API",
    version="1.0.0",
)

# Swagger UI will show the merged schema
app.enable_swagger(path="/docs")


def handler(event, context):
    return app.resolve(event, context)
