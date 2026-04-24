import asyncio

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver

app = APIGatewayHttpResolver()


async def fetch_profile(user_id: str) -> dict:
    await asyncio.sleep(0)  # simulate async I/O (e.g., DynamoDB, HTTP call)
    return {"user_id": user_id, "name": "John"}


async def fetch_orders(user_id: str) -> list:
    await asyncio.sleep(0)
    return [{"order_id": "123", "total": 99.99}]


@app.get("/dashboard/<user_id>")
async def get_dashboard(user_id: str):
    profile, orders = await asyncio.gather(  # (1)!
        fetch_profile(user_id),
        fetch_orders(user_id),
    )
    return {"profile": profile, "orders": orders}


def lambda_handler(event, context):
    return asyncio.run(app.resolve_async(event, context))
