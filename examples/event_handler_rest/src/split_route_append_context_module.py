import requests
from requests import Response

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.event_handler.api_gateway import Router

tracer = Tracer()
router = Router()

endpoint = "https://jsonplaceholder.typicode.com/todos"


@router.get("/todos")
@tracer.capture_method
def get_todos():
    is_admin: bool = router.context.get("is_admin", False)
    todos = {}

    if is_admin:
        todos: Response = requests.get(endpoint)
        todos.raise_for_status()
        todos = todos.json()[:10]

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos}
