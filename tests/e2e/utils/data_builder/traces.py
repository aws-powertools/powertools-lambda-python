from __future__ import annotations

from typing import Any


def build_trace_default_query(function_name: str) -> str:
    return f'service(id(name: "{function_name}"))'


def build_put_annotations_input(**annotations: str) -> list[dict]:
    """Create trace annotations input to be used with Tracer.put_annotation()

    Parameters
    ----------
    annotations : str
        annotations in key=value form

    Returns
    -------
    List[Dict]
        List of put annotations input
    """
    return [{"key": key, "value": value} for key, value in annotations.items()]


def build_put_metadata_input(namespace: str | None = None, **metadata: Any) -> list[dict]:
    """Create trace metadata input to be used with Tracer.put_metadata()

    All metadata will be under `test` namespace

    Parameters
    ----------
    metadata : Any
        metadata in key=value form

    Returns
    -------
    List[Dict]
        List of put metadata input
    """
    return [{"key": key, "value": value, "namespace": namespace} for key, value in metadata.items()]
