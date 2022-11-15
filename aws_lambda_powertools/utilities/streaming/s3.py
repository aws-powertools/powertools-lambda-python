import io
import logging
import typing
from typing import TYPE_CHECKING, List, Literal, Optional, Sequence, Union, overload

import boto3
from botocore.response import StreamingBody

from aws_lambda_powertools.utilities.streaming.transformations.base import (
    BaseTransform,
    T,
)
from aws_lambda_powertools.utilities.streaming.transformations.gzip import GzipTransform
from aws_lambda_powertools.utilities.streaming.transformations.json import JsonTransform

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Object, S3ServiceResource

logger = logging.getLogger(__name__)


class _S3Proxy(io.RawIOBase):
    def __init__(
        self, bucket: str, key: str, version_id: Optional[str] = None, boto3_s3_resource=Optional["S3ServiceResource"]
    ):
        self.bucket = bucket
        self.key = key
        self.version_id = version_id

        self._position = 0
        self._size: Optional[int] = None

        self._s3_object: Optional["Object"] = None
        self._s3_resource: Optional["S3ServiceResource"] = boto3_s3_resource
        self._raw_stream: Optional[StreamingBody] = None

    @property
    def s3_resource(self) -> "S3ServiceResource":
        if self._s3_resource is None:
            self._s3_resource = boto3.resource("s3")
        return self._s3_resource

    @property
    def s3_object(self) -> "Object":
        if self._s3_object is None:
            if self.version_id is not None:
                self._s3_object = self.s3_resource.ObjectVersion(
                    bucket_name=self.bucket, object_key=self.key, id=self.version_id
                ).Object()
            else:
                self._s3_object = self.s3_resource.Object(bucket_name=self.bucket, key=self.key)

        return self._s3_object

    @property
    def size(self) -> int:
        if self._size is None:
            self._size = self.s3_object.content_length
        return self._size

    @property
    def raw_stream(self) -> StreamingBody:
        if self._raw_stream is None:
            range_header = "bytes=%d-" % self._position
            logging.debug(f"Starting new stream at {range_header}...")
            self._raw_stream = self.s3_object.get(Range=range_header)["Body"]

        return self._raw_stream

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        current_position = self._position

        if whence == io.SEEK_SET:
            self._position = offset
        elif whence == io.SEEK_CUR:
            self._position += offset
        elif whence == io.SEEK_END:
            self._position = self.size + offset
        else:
            raise ValueError(f"invalid whence ({whence}, should be {io.SEEK_SET}, {io.SEEK_CUR}, {io.SEEK_END})")

        # If we changed the position in the stream, we should invalidate the existing stream
        # and open a new one on the next read
        if current_position != self._position and self._raw_stream is not None:
            self._raw_stream.close()
            self._raw_stream = None

        return self._position

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def read(self, size: Optional[int] = -1) -> Optional[bytes]:
        size = None if size == -1 else size
        data = self.raw_stream.read(size)
        if data is not None:
            self._position += len(data)
        return data

    def readline(self, size: Optional[int] = None) -> bytes:
        data = self.raw_stream.readline(size)
        self._position += len(data)
        return data

    @property
    def closed(self) -> bool:
        return self.raw_stream.closed

    def __next__(self):
        return self.raw_stream.__next__()

    def __iter__(self):
        return self.raw_stream.__iter__()


class S3Object(io.RawIOBase):
    def __init__(
        self,
        bucket: str,
        key: str,
        version_id: Optional[str] = None,
        boto3_s3_resource: Optional["S3ServiceResource"] = None,
        gunzip: Optional[bool] = False,
        json: Optional[bool] = False,
    ):
        self.bucket = bucket
        self.key = key
        self.version_id = version_id
        self.raw_stream = _S3Proxy(bucket=bucket, key=key, version_id=version_id, boto3_s3_resource=boto3_s3_resource)

        self._transformed_stream: Optional[io.RawIOBase] = None
        self._data_transformations: List[BaseTransform] = []
        if gunzip:
            self._data_transformations.append(GzipTransform())
        if json:
            self._data_transformations.append(JsonTransform())

    @property
    def size(self) -> int:
        return self.raw_stream.size

    @property
    def transformed_stream(self) -> io.RawIOBase:
        if self._transformed_stream is None:
            # Apply all the transformations
            transformed_stream = self.raw_stream
            for transformation in self._data_transformations:
                transformed_stream = transformation.transform(transformed_stream)

            self._transformed_stream = transformed_stream

        return self._transformed_stream

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        return self.raw_stream.seek(offset, whence)

    def seekable(self) -> bool:
        return self.raw_stream.seekable()

    def readable(self) -> bool:
        return self.raw_stream.readable()

    def writable(self) -> bool:
        return self.raw_stream.writable()

    def tell(self) -> int:
        return self.raw_stream.tell()

    @property
    def closed(self) -> bool:
        return self.raw_stream.closed

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.raw_stream.close()

        # Also close transformed stream if there are any transformations
        if self.raw_stream != self._transformed_stream and self._transformed_stream is not None:
            self._transformed_stream.close()

    def read(self, size: int = -1) -> Optional[bytes]:
        return self.transformed_stream.read(size)

    def readline(self, size: Optional[int] = None) -> bytes:
        return self.transformed_stream.readline(size)

    def __next__(self):
        return self.transformed_stream.__next__()

    def __iter__(self):
        return self.transformed_stream.__iter__()

    @overload
    def transform(
        self, transformations: Union[BaseTransform[T], Sequence[BaseTransform[T]]], in_place: Literal[True]
    ) -> T:
        pass

    @overload
    def transform(
        self, transformations: Union[BaseTransform[T], Sequence[BaseTransform[T]]], in_place: Literal[False]
    ) -> None:
        pass

    @overload
    def transform(self, transformations: Union[BaseTransform[T], Sequence[BaseTransform[T]]]) -> T:
        pass

    def transform(
        self, transformations: Union[BaseTransform[T], Sequence[BaseTransform[T]]], in_place: Optional[bool] = False
    ) -> Optional[T]:
        if self.tell() != 0:
            raise ValueError(f"Cannot add transformations to a read object. Already read {self.tell()} bytes")

        # Make transformations always be a sequence to make mypy happy
        if not isinstance(transformations, Sequence):
            transformations = [transformations]

        if in_place:
            self._data_transformations.extend(transformations)

            # Invalidate transformed stream
            self._transformed_stream = None
            return None
        else:
            # Tell MyPy that raw_stream actually implements T (bound to io.RawIOBase)
            stream = typing.cast(T, self.raw_stream)
            for transformation in transformations:
                stream = transformation.transform(stream)
            return stream
