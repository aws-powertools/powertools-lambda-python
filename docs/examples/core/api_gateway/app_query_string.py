from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/hello")
def get_hello_you():
    query_strings_as_dict = app.current_event.query_string_parameters
    json_payload = app.current_event.json_body
    payload = app.current_event.body

    name = app.current_event.get_query_string_value(name="name", default_value="")
    return {"message": f"hello {name}"}


def lambda_handler(event, context):
    return app.resolve(event, context)
