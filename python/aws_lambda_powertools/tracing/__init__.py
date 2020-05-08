"""Tracing utility
"""
from aws_xray_sdk.ext.aiohttp.client import aws_xray_trace_config as aiohttp_trace_config

from .tracer import Tracer

__all__ = ["Tracer", "aiohttp_trace_config"]
