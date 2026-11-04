import asyncio
import os

import httpx

from aws_lambda_powertools.utilities.circuit_breaker import CircuitBreakerConfig, CircuitInfo, circuit_breaker
from aws_lambda_powertools.utilities.circuit_breaker.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("CIRCUIT_BREAKER_TABLE", "")
persistence = CircuitBreakerDynamoDBPersistence(table_name=table)
config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)


async def cached_quote(symbol: str, circuit: CircuitInfo) -> dict:
    # Async callbacks are awaited; sync callbacks work too.
    return {"symbol": symbol, "price": None, "circuit": circuit.state.value}


@circuit_breaker(
    name="quotes-api",
    persistence_store=persistence,
    config=config,
    on_circuit_open=cached_quote,
)
async def get_quote(symbol: str) -> dict:
    # The coroutine is awaited inside the circuit, so a failure raised here counts
    # towards failure_threshold just like it does for a regular function.
    async with httpx.AsyncClient(timeout=2) as client:
        response = await client.get(f"https://quotes.example.com/{symbol}")
        response.raise_for_status()
        return response.json()


def lambda_handler(event: dict, context: LambdaContext):
    return asyncio.run(get_quote(event["symbol"]))
