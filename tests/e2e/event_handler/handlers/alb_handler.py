from typing import Dict

from aws_lambda_powertools.event_handler import ALBResolver, Response, content_types

app = ALBResolver()


@app.post("/todos")
def hello():
    payload: Dict = app.current_event.json_body

    return Response(
        status_code=200,
        content_type=content_types.TEXT_PLAIN,
        body="Hello world",
        cookies=payload["cookies"],
        headers=payload["headers"],
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
