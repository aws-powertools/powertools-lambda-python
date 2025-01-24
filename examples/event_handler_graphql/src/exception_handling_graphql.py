from aws_lambda_powertools.event_handler import AppSyncResolver

app = AppSyncResolver()


@app.exception_handler(ValueError)
def handle_value_error(ex: ValueError):
    return {"message": "error"}


@app.resolver(field_name="createSomething")
def create_something():
    raise ValueError("Raising an exception")


def lambda_handler(event, context):
    return app.resolve(event, context)
