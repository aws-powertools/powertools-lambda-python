import asyncio

from aws_lambda_powertools.event_handler import AppSyncResolver

app = AppSyncResolver()


@app.resolver(field_name="createSomething")
async def create_something_async():
    await asyncio.sleep(1)  # Do async stuff
    return "created this value"
