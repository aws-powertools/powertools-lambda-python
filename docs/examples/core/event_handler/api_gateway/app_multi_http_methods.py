from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


# PUT and POST HTTP requests to the path /hello will route to this function
@app.route("/hello", method=["PUT", "POST"])
@tracer.capture_method
def get_hello_you():
    name = app.current_event.json_body.get("name")
    return {"message": f"hello {name}"}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
