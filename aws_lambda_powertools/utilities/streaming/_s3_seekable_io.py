import io
import logging
from typing import IO, TYPE_CHECKING, AnyStr, Iterable, List, Optional

import boto3
from botocore.response import StreamingBody

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_s3.service_resource import Object

logger = logging.getLogger(__name__)


class _S3SeekableIO(IO[bytes]):
    """
    _S3SeekableIO wraps boto3.StreamingBody to allow for seeking. Seeking is achieved by closing the
    existing connection and re-opening a new one, passing the correct HTTP Range header.

    Parameters
    ----------
    bucket: str
        The S3 bucket
    key: str
        The S3 key
    version_id: str, optional
        A version ID of the object, when the S3 bucket is versioned
    boto3_s3_resource: S3ServiceResource, optional
        An optional boto3 S3 resource. If missing, a new one will be created.
    """

    def __init__(
        self, bucket: str, key: str, version_id: Optional[str] = None, boto3_s3_resource=Optional["S3ServiceResource"]
    ):
        self.bucket = bucket
        self.key = key
        self.version_id = version_id

        # Holds the current position in the stream
        self._position = 0

        # Stores the closed state of the stream
        self._closed: bool = False

        # Caches the size of the object
        self._size: Optional[int] = None

        self._s3_object: Optional["Object"] = None
        self._s3_resource: Optional["S3ServiceResource"] = boto3_s3_resource
        self._raw_stream: Optional[StreamingBody] = None

    @property
    def s3_resource(self) -> "S3ServiceResource":
        """
        Returns a boto3 S3ServiceResource
        """
        if self._s3_resource is None:
            self._s3_resource = boto3.resource("s3")
        return self._s3_resource

    @property
    def s3_object(self) -> "Object":
        """
        Returns a boto3 S3Object
        """
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
        """
        Retrieves the size of the S3 object
        """
        if self._size is None:
            self._size = self.s3_object.content_length
        return self._size

    @property
    def raw_stream(self) -> StreamingBody:
        """
        Returns the boto3 StreamingBody, starting the stream from the seeked position.
        """
        if self._raw_stream is None:
            range_header = "bytes=%d-" % self._position
            logging.debug(f"Starting new stream at {range_header}...")
            self._raw_stream = self.s3_object.get(Range=range_header)["Body"]
            self._closed = False

        return self._raw_stream

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """
        Seeks the current object, invalidating the underlying stream if the position changes.
        """
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

    def tell(self) -> int:
        return self._position

    def read(self, size: Optional[int] = -1) -> bytes:
        size = None if size == -1 else size
        data = self.raw_stream.read(size)
        if data is not None:
            self._position += len(data)
        return data

    def readline(self, size: Optional[int] = None) -> bytes:
        data = self.raw_stream.readline(size)
        self._position += len(data)
        return data

    def readlines(self, hint: int = -1) -> List[bytes]:
        # boto3's StreamingResponse doesn't implement the "hint" parameter
        data = self.raw_stream.readlines()
        self._position += sum(len(line) for line in data)
        return data

    @property
    def closed(self) -> bool:
        return self._closed

    def __next__(self):
        return self.raw_stream.__next__()

    def __iter__(self):
        return self.raw_stream.__iter__()

    def __enter__(self):
        return self

    def __exit__(self, *kwargs):
        self.close()

    def close(self) -> None:
        self.raw_stream.close()
        self._closed = True

    def fileno(self) -> int:
        raise NotImplementedError()

    def flush(self) -> None:
        raise NotImplementedError()

    def isatty(self) -> bool:
        return False

    def truncate(self, size: Optional[int] = 0) -> int:
        raise NotImplementedError()

    def write(self, data: AnyStr) -> int:
        raise NotImplementedError()

    def writelines(self, lines: Iterable[AnyStr]) -> None:
        raise NotImplementedError()
