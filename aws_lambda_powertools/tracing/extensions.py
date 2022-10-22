def aiohttp_trace_config():
    """aiohttp extension for X-Ray (aws_xray_trace_config)

    It expects you to have aiohttp as a dependency.

    Returns
    -------
    TraceConfig
        aiohttp trace config
    """
    from aws_xray_sdk.ext.aiohttp.client import (
        aws_xray_trace_config,  # pragma: no cover
    )

    aws_xray_trace_config.__doc__ = "aiohttp extension for X-Ray (aws_xray_trace_config)"  # pragma: no cover

    return aws_xray_trace_config()  # pragma: no cover
