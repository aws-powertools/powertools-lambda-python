from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler import AppSyncEventsResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncEventsResolver()


@app.async_on_publish("/default/channel1")
async def handle_channel1_publish(payload: dict[str, Any]):
    return await async_process_data(payload)


async def async_process_data(payload: dict[str, Any]):
    await asyncio.sleep(0.1)
    return {"processed": payload, "async": True}


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
