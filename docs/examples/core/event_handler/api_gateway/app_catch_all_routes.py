from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get(".+")
def catch_any_route_after_any():
    return {"path_received": app.current_event.path}


def lambda_handler(event, context):
    return app.resolve(event, context)
