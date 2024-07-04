from aws_lambda_powertools.event_handler import (
    ALBResolver,
    Response,
)

app = ALBResolver()


@app.get("/todos_with_no_body")
def todos():
    return Response(
        status_code=200,
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
