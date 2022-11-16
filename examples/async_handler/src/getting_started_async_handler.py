import asyncio

from aws_lambda_powertools.asynchrony import async_lambda_handler
from aws_lambda_powertools.utilities.typing import LambdaContext


@async_lambda_handler
async def lambda_handler(event, context: LambdaContext):
    await asyncio.sleep(1)
    return 'awaited for 1 second'
