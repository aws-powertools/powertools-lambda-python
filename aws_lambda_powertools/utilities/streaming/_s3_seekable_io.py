import io
import logging
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Iterable,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import boto3

from aws_lambda_powertools.utilities.streaming.compat import PowertoolsStreamingBody

if TYPE_CHECKING:
    from mmap import mmap

    from mypy_boto3_s3 import Client

    _CData = TypeVar("_CData")

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
    boto3_client: boto3 S3 Client, optional
        An optional boto3 S3 client. If missing, a new one will be created.
    sdk_options: dict, optional
        Dictionary of options that will be passed to the S3 Client get_object API call
    """

    def __init__(
        self, bucket: str, key: str, version_id: Optional[str] = None, boto3_client=Optional["Client"], **sdk_options
    ):
        self.bucket = bucket
        self.key = key

        # Holds the current position in the stream
        self._position = 0

        # Stores the closed state of the stream
        self._closed: bool = False

        # Caches the size of the object
        self._size: Optional[int] = None

        self._s3_client: Optional["Client"] = boto3_client
        self._raw_stream: Optional[PowertoolsStreamingBody] = None

        self._sdk_options = sdk_options
        self._sdk_options["Bucket"] = bucket
        self._sdk_options["Key"] = key
        if version_id is not None:
            self._sdk_options["VersionId"] = version_id

    @property
    def s3_client(self) -> "Client":
        """
        Returns a boto3 S3 client
        """
        if self._s3_client is None:
            self._s3_client = boto3.client("s3")
        return self._s3_client

    @property
    def size(self) -> int:
        """
        Retrieves the size of the S3 object
        """
        if self._size is None:
            logger.debug("Getting size of S3 object")
            self._size = self.s3_client.head_object(**self._sdk_options).get("ContentLength", 0)
        return self._size

    @property
    def raw_stream(self) -> PowertoolsStreamingBody:
        """
        Returns the boto3 StreamingBody, starting the stream from the seeked position.
        """
        if self._raw_stream is None:
            range_header = f"bytes={self._position}-"
            logger.debug(f"Starting new stream at {range_header}")
            self._raw_stream = self.s3_client.get_object(Range=range_header, **self._sdk_options).get("Body")
            self._closed = False

        return cast(PowertoolsStreamingBody, self._raw_stream)

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

        # Invalidate the existing stream, so a new one will be open on the next IO operation.
        #
        # Some consumers of this class might call seek multiple times, without affecting the net position.
        # zipfile.ZipFile does this often. If we just blindly invalidated the stream, we would have to re-open
        # an S3 HTTP connection just to continue reading on the same position as before, which would be inefficient.
        #
        # So we only invalidate it if there's a net position change after seeking, and we have an existing S3 connection
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
        raise NotImplementedError("this stream is not backed by a file descriptor")

    def flush(self) -> None:
        raise NotImplementedError("this stream is not writable")

    def isatty(self) -> bool:
        return False

    def truncate(self, size: Optional[int] = 0) -> int:
        raise NotImplementedError("this stream is not writable")

    def write(self, data: Union[bytes, Union[bytearray, memoryview, Sequence[Any], "mmap", "_CData"]]) -> int:
        raise NotImplementedError("this stream is not writable")

    def writelines(
        self,
        data: Iterable[Union[bytes, Union[bytearray, memoryview, Sequence[Any], "mmap", "_CData"]]],
    ) -> None:
        raise NotImplementedError("this stream is not writable")
