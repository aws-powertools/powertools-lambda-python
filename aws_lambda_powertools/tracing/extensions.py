def aiohttp_trace_config():
    """aiohttp extension for X-Ray (aws_xray_trace_config)

    It expects you to have aiohttp as a dependency.

    Example
    -------

    ```python
    import asyncio
    import aiohttp

    from aws_lambda_powertools import Tracer
    from aws_lambda_powertools.tracing import aiohttp_trace_config

    tracer = Tracer()

    async def aiohttp_task():
        async with aiohttp.ClientSession(trace_configs=[aiohttp_trace_config()]) as session:
            async with session.get("https://httpbin.org/json") as resp:
                resp = await resp.json()
                return resp
    ```

    Returns
    -------
    TraceConfig
        aiohttp trace config
    """
    from aws_xray_sdk.ext.aiohttp.client import aws_xray_trace_config  # pragma: no cover

    aws_xray_trace_config.__doc__ = "aiohttp extension for X-Ray (aws_xray_trace_config)"  # pragma: no cover

    return aws_xray_trace_config()  # pragma: no cover
