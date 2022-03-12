from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/hello")
def get_hello_you():
    headers_as_dict = app.current_event.headers
    name = app.current_event.get_header_value(name="X-Name", default_value="")

    return {"message": f"hello {name}"}


def lambda_handler(event, context):
    return app.resolve(event, context)
