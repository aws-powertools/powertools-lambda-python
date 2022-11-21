from __future__ import annotations

import io
from typing import (
    IO,
    TYPE_CHECKING,
    AnyStr,
    Iterable,
    List,
    Optional,
    Sequence,
    cast,
    overload,
)

from typing_extensions import Literal

from aws_lambda_powertools.utilities.streaming._s3_seekable_io import _S3SeekableIO
from aws_lambda_powertools.utilities.streaming.transformations import (
    CsvTransform,
    GzipTransform,
)
from aws_lambda_powertools.utilities.streaming.transformations.base import (
    BaseTransform,
    T,
)

if TYPE_CHECKING:
    from mypy_boto3_s3 import Client


class S3Object(IO[bytes]):
    """
    Seekable and streamable S3 Object reader.

    S3Object implements the IO[bytes], backed by a seekable S3 streaming.

    Parameters
    ----------
    bucket: str
        The S3 bucket
    key: str
        The S3 key
    version_id: str, optional
        A version ID of the object, when the S3 bucket is versioned
    boto3_s3_client: S3Client, optional
        An optional boto3 S3 client. If missing, a new one will be created.
    gunzip: bool, optional
        Enables the Gunzip data transformation
    csv: bool, optional
        Enables the CSV data transformation

    Example
    -------

    ** Reads a line from an S3, loading as little data as necessary

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>>
        >>> line: bytes = S3Object(bucket="bucket", key="key").readline()
        >>>
        >>> print(line)

    """

    def __init__(
        self,
        bucket: str,
        key: str,
        version_id: Optional[str] = None,
        boto3_s3_client: Optional["Client"] = None,
        gunzip: Optional[bool] = False,
        csv: Optional[bool] = False,
    ):
        self.bucket = bucket
        self.key = key
        self.version_id = version_id

        # The underlying seekable IO, where all the magic happens
        self.raw_stream = _S3SeekableIO(bucket=bucket, key=key, version_id=version_id, boto3_s3_client=boto3_s3_client)

        # Stores the list of data transformations
        self._data_transformations: List[BaseTransform] = []
        if gunzip:
            self._data_transformations.append(GzipTransform())
        if csv:
            self._data_transformations.append(CsvTransform())

        # Stores the cached transformed stream
        self._transformed_stream: Optional[IO[bytes]] = None

    @property
    def size(self) -> int:
        """
        Retrieves the size of the underlying S3 object
        """
        return self.raw_stream.size

    @property
    def transformed_stream(self) -> IO[bytes]:
        """
        Returns a IO[bytes] stream with all the data transformations applied in order
        """
        if self._transformed_stream is None:
            # Apply all the transformations
            transformed_stream = self.raw_stream
            for transformation in self._data_transformations:
                transformed_stream = transformation.transform(transformed_stream)

            self._transformed_stream = transformed_stream

        return self._transformed_stream

    @overload
    def transform(self, transformations: BaseTransform[T] | Sequence[BaseTransform[T]], in_place: Literal[True]) -> T:
        pass

    @overload
    def transform(
        self, transformations: BaseTransform[T] | Sequence[BaseTransform[T]], in_place: Literal[False]
    ) -> None:
        pass

    @overload
    def transform(self, transformations: BaseTransform[T] | Sequence[BaseTransform[T]]) -> T:
        pass

    def transform(
        self, transformations: BaseTransform[T] | Sequence[BaseTransform[T]], in_place: Optional[bool] = False
    ) -> Optional[T]:
        """
        Applies one or more data transformations to the stream.

        Parameters
        ----------
        transformations: BaseTransform[T] | Sequence[BaseTransform[T]]
            One or more transformations to apply. Transformations are applied in the same order as they are declared.
        in_place: bool, optional
            Transforms the stream in place, instead of returning a new stream object. Defaults to false.

        Returns
        -------
        T[bound=IO[bytes]], optional
            If in_place is False, returns an IO[bytes] object representing the transformed stream
        """
        if self.tell() != 0:
            raise ValueError(f"Cannot add transformations to a read object. Already read {self.tell()} bytes")

        # Make transformations always be a sequence to make mypy happy
        if not isinstance(transformations, Sequence):
            transformations = [transformations]

        if in_place:
            self._data_transformations.extend(transformations)

            # Invalidate any existing transformed stream.
            # It will be created again next time it's accessed.
            self._transformed_stream = None
            return None
        else:
            # Tell mypy that raw_stream actually implements T (bound to IO[bytes])
            stream = cast(T, self.raw_stream)
            for transformation in transformations:
                stream = transformation.transform(stream)
            return stream

    # From this point on, we're just implementing all the standard methods on the IO[bytes] type.
    # There's no magic here, just delegating all the calls to our transformed_stream.
    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        return self.transformed_stream.seek(offset, whence)

    def seekable(self) -> bool:
        return self.transformed_stream.seekable()

    def readable(self) -> bool:
        return self.transformed_stream.readable()

    def writable(self) -> bool:
        return self.transformed_stream.writable()

    def tell(self) -> int:
        return self.transformed_stream.tell()

    @property
    def closed(self) -> bool:
        return self.transformed_stream.closed

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.raw_stream.close()

        # Also close transformed stream if there are any transformations
        if self.raw_stream != self._transformed_stream and self._transformed_stream is not None:
            self._transformed_stream.close()

    def read(self, size: int = -1) -> bytes:
        return self.transformed_stream.read(size)

    def readline(self, size: Optional[int] = -1) -> bytes:
        return self.transformed_stream.readline()

    def readlines(self, hint: int = -1) -> List[bytes]:
        return self.transformed_stream.readlines(hint)

    def __next__(self):
        return self.transformed_stream.__next__()

    def __iter__(self):
        return self.transformed_stream.__iter__()

    def fileno(self) -> int:
        raise NotImplementedError("this stream is not backed by a file descriptor")

    def flush(self) -> None:
        raise NotImplementedError("this stream is not writable")

    def isatty(self) -> bool:
        return False

    def truncate(self, size: Optional[int] = 0) -> int:
        raise NotImplementedError("this stream is not writable")

    def write(self, data: AnyStr) -> int:
        raise NotImplementedError("this stream is not writable")

    def writelines(self, lines: Iterable[AnyStr]) -> None:
        raise NotImplementedError("this stream is not writable")
