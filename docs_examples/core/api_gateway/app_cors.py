from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer()
logger = Logger()

cors_config = CORSConfig(allow_origin="https://example.com", max_age=300)
app = APIGatewayRestResolver(cors=cors_config)


@app.get("/hello/<name>")
@tracer.capture_method
def get_hello_you(name):
    return {"message": f"hello {name}"}


@app.get("/hello", cors=False)  # optionally exclude CORS from response, if needed
@tracer.capture_method
def get_hello_no_cors_needed():
    return {"message": "hello, no CORS needed for this path ;)"}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
