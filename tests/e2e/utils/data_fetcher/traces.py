import json
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

import boto3
from botocore.paginate import PageIterator
from mypy_boto3_xray.client import XRayClient
from mypy_boto3_xray.type_defs import TraceSummaryTypeDef
from pydantic import BaseModel
from retry import retry


class TraceSubsegment(BaseModel):
    id: str  # noqa: A003 VNE003  # id is a field we can't change
    name: str
    start_time: float
    end_time: float
    aws: Optional[dict]
    subsegments: Optional[List["TraceSubsegment"]]
    annotations: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Dict[str, Any]]]


class TraceDocument(BaseModel):
    id: str  # noqa: A003 VNE003  # id is a field we can't change
    name: str
    start_time: float
    end_time: float
    trace_id: str
    parent_id: Optional[str]
    aws: Dict
    origin: str
    subsegments: Optional[List[TraceSubsegment]]


class TraceFetcher:
    default_exclude_seg_name: List = ["Initialization", "Invocation", "Overhead"]

    def __init__(
        self,
        filter_expression: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        xray_client: Optional[XRayClient] = None,
        exclude_segment_name: Optional[List[str]] = None,
        resource_name: Optional[List[str]] = None,
        origin: Optional[List[str]] = None,
        minimum_traces: int = 1,
    ):
        """Fetch and expose traces from X-Ray based on parameters

        Data is recursively fetched in the following order:

        * Trace summaries
        * Trace IDs
        * Traces
        * Segments
        * Subsegments
        * Nested Subsegments

        Parameters
        ----------
        filter_expression : str
            AWS X-Ray Filter Expressions
            see: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html
        start_date : datetime
            Start date range to filter traces
        end_date : Optional[datetime], optional
            End date range to filter traces, by default 5 minutes past start_date
        xray_client : Optional[XRayClient], optional
            AWS X-Ray SDK Client, by default boto3.client('xray')
        exclude_segment_name : Optional[List[str]], optional
            Name of segments to exclude, by default ["Initialization", "Invocation", "Overhead"]
        resource_name : Optional[List[str]], optional
            Name of resource to filter traces (e.g., function name), by default None
        origin : Optional[List[str]], optional
            Trace origin name to filter traces, by default ["AWS::Lambda::Function"]
        minimum_traces : int
            Minimum number of traces to be retrieved before exhausting retry attempts
        """
        self.filter_expression = filter_expression
        self.start_date = start_date
        self.end_date = end_date or self.start_date + timedelta(minutes=5)
        self.xray_client: XRayClient = xray_client or boto3.client("xray")
        self.trace_documents: Dict[str, TraceDocument] = {}
        self.subsegments: List[TraceSubsegment] = []
        self.exclude_segment_name = exclude_segment_name or self.default_exclude_seg_name
        self.resource_name = resource_name
        self.origin = origin or ["AWS::Lambda::Function"]
        self.annotations: List[Dict[str, Any]] = []
        self.metadata: List[Dict[str, Dict[str, Any]]] = []
        self.minimum_traces = minimum_traces

        paginator = self.xray_client.get_paginator("get_trace_summaries")
        pages = paginator.paginate(
            StartTime=self.start_date,
            EndTime=self.end_date,
            TimeRangeType="Event",
            Sampling=False,
            FilterExpression=self.filter_expression,
        )

        trace_ids = self._get_trace_ids(pages)
        self.trace_documents = self._get_trace_documents(trace_ids)
        self.subsegments = self._get_subsegments()

    def get_annotation(self, key: str, value: Optional[any] = None) -> List:
        return [
            annotation
            for annotation in self.annotations
            if (value is not None and annotation.get(key) == value) or (value is None and key in annotation)
        ]

    def get_metadata(self, key: str, namespace: str = "") -> List[Dict[str, Any]]:
        seen = []
        for meta in self.metadata:
            metadata = meta.get(namespace, {})
            if key in metadata:
                seen.append(metadata)
        return seen

    def get_subsegment(self, name: str) -> List:
        return [seg for seg in self.subsegments if seg.name == name]

    def _find_nested_subsegments(self, subsegments: List[TraceSubsegment]) -> Generator[TraceSubsegment, None, None]:
        """Recursively yield any subsegment that we might be interested.

        It excludes any subsegments contained in exclude_segment_name.
        Since these are nested, subsegment name might be '## lambda_handler'.

        It also populates annotations and metadata nested in subsegments.

        Parameters
        ----------
        subsegment : TraceSubsegment
            subsegment to traverse
        seen : List
            list of subsegments to be updated
        """
        for seg in subsegments:
            if seg.name not in self.exclude_segment_name:
                if seg.annotations:
                    self.annotations.append(seg.annotations)

                if seg.metadata:
                    self.metadata.append(seg.metadata)

                yield seg

            if seg.subsegments:
                # recursively iterate over any arbitrary number of subsegments
                yield from self._find_nested_subsegments(seg.subsegments)

    def _get_subsegments(self) -> List[TraceSubsegment]:
        """Find subsegments and potentially any nested subsegments

        It excludes any subsegments contained in exclude_segment_name.
        Since these are top-level, subsegment name might be 'Overhead/Invocation, etc.'.

        Returns
        -------
        List[TraceSubsegment]
            List of subsegments
        """
        seen = []
        for document in self.trace_documents.values():
            if document.subsegments:
                seen.extend(self._find_nested_subsegments(document.subsegments))

        return seen

    def _get_trace_ids(self, pages: PageIterator) -> List[str]:
        """Get list of trace IDs found

        Parameters
        ----------
        pages : PageIterator
            Paginated streaming response from AWS X-Ray

        Returns
        -------
        List[str]
            Trace IDs

        Raises
        ------
        ValueError
            When no traces are available within time range and filter expression
        """
        summaries: List[TraceSummaryTypeDef] = [trace["TraceSummaries"] for trace in pages if trace["TraceSummaries"]]
        if not summaries:
            raise ValueError("Empty response from X-Ray. Repeating...")

        trace_ids = [trace["Id"] for trace in summaries[0]]  # type: ignore[index] # TypedDict not being recognized
        if len(trace_ids) < self.minimum_traces:
            raise ValueError(
                f"Number of traces found doesn't meet minimum required ({self.minimum_traces}). Repeating...",
            )

        return trace_ids

    def _get_trace_documents(self, trace_ids: List[str]) -> Dict[str, TraceDocument]:
        """Find trace documents available in each trace segment

        Returns
        -------
        Dict[str, TraceDocument]
            Trace documents grouped by their ID
        """
        traces = self.xray_client.batch_get_traces(TraceIds=trace_ids)
        documents: Dict = {}
        segments = [seg for trace in traces["Traces"] for seg in trace["Segments"]]
        for seg in segments:
            trace_document = TraceDocument(**json.loads(seg["Document"]))
            if trace_document.origin in self.origin or trace_document.name == self.resource_name:
                documents[trace_document.id] = trace_document
        return documents


@retry(ValueError, delay=5, jitter=1.5, tries=10)
def get_traces(
    filter_expression: str,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    xray_client: Optional[XRayClient] = None,
    exclude_segment_name: Optional[List[str]] = None,
    resource_name: Optional[List[str]] = None,
    origin: Optional[List[str]] = None,
    minimum_traces: int = 1,
) -> TraceFetcher:
    """Fetch traces from AWS X-Ray

    Parameters
    ----------
    filter_expression : str
        AWS X-Ray Filter Expressions
        see: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html
    start_date : datetime
        Start date range to filter traces
    end_date : Optional[datetime], optional
        End date range to filter traces, by default 5 minutes past start_date
    xray_client : Optional[XRayClient], optional
        AWS X-Ray SDK Client, by default boto3.client('xray')
    exclude_segment_name : Optional[List[str]], optional
        Name of segments to exclude, by default ["Initialization", "Invocation", "Overhead"]
    resource_name : Optional[List[str]], optional
        Name of resource to filter traces (e.g., function name), by default None
    origin : Optional[List[str]], optional
        Trace origin name to filter traces, by default ["AWS::Lambda::Function"]
    minimum_traces : int
        Minimum number of traces to be retrieved before exhausting retry attempts

    Returns
    -------
    TraceFetcher
        TraceFetcher instance with trace data available as properties and methods
    """
    return TraceFetcher(
        filter_expression=filter_expression,
        start_date=start_date,
        end_date=end_date,
        xray_client=xray_client,
        exclude_segment_name=exclude_segment_name,
        resource_name=resource_name,
        origin=origin,
        minimum_traces=minimum_traces,
    )
