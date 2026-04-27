import asyncio

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver

app = APIGatewayHttpResolver()


@app.get("/todos/<todo_id>")
async def get_todo(todo_id: str):  # (1)!
    # Async handlers can use await for non-blocking I/O
    await asyncio.sleep(0)  # simulate async I/O
    return {"todo_id": todo_id, "completed": False}


@app.get("/health")
def health():  # (2)!
    return {"status": "ok"}


def lambda_handler(event, context):
    return asyncio.run(app.resolve_async(event, context))  # (3)!
