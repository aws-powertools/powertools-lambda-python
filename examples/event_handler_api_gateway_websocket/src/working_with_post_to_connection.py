import boto3
import my_connection_store  # (1)!
from botocore.config import Config

from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

boto_config = Config(connect_timeout=3, read_timeout=5, retries={"total_max_attempts": 2})
app = APIGatewayWebSocketResolver()


def start_report_generation(report_id: str, connection_id: str) -> None: ...  # e.g. start a Step Functions execution


@app.on_connect()
def connect():
    request_context = app.current_event.request_context
    my_connection_store.save(request_context.connection_id, request_context.callback_url)  # (2)!


@app.on_disconnect()
def disconnect():
    my_connection_store.delete(app.current_event.request_context.connection_id)


@app.route("submitReport")
def submit_report():
    request = app.current_event.json_body
    start_report_generation(request["reportId"], app.current_event.request_context.connection_id)
    return {"status": "accepted"}  # (3)!


@app.route("broadcast")
def broadcast():
    client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=app.current_event.request_context.callback_url,  # (4)!
        config=boto_config,
    )
    message: str = app.current_event.json_body["message"]
    for connection_id in my_connection_store.all_connection_ids():
        try:
            client.post_to_connection(ConnectionId=connection_id, Data=message.encode())
        except client.exceptions.GoneException:
            my_connection_store.delete(connection_id)


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
