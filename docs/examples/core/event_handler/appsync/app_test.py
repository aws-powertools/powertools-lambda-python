from aws_lambda_powertools.event_handler import AppSyncResolver

app = AppSyncResolver()


@app.resolver(field_name="createSomething")
def create_something():
    return "created this value"
