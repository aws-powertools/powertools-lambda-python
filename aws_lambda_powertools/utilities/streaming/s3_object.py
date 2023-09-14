from __future__ import annotations

import io
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
    overload,
)

from aws_lambda_powertools.shared.types import Literal
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
    from mmap import mmap

    from mypy_boto3_s3 import Client

    _CData = TypeVar("_CData")


# Maintenance: almost all this logic should be moved to a base class
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
    boto3_client: S3Client, optional
        An optional boto3 S3 client. If missing, a new one will be created.
    is_gzip: bool, optional
        Enables the Gunzip data transformation
    is_csv: bool, optional
        Enables the CSV data transformation
    sdk_options: dict, optional
        Dictionary of options that will be passed to the S3 Client get_object API call

    Example
    -------

    **Reads a line from an S3, loading as little data as necessary:**

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
        boto3_client: Optional["Client"] = None,
        is_gzip: Optional[bool] = False,
        is_csv: Optional[bool] = False,
        **sdk_options,
    ):
        self.bucket = bucket
        self.key = key
        self.version_id = version_id

        # The underlying seekable IO, where all the magic happens
        self.raw_stream = _S3SeekableIO(
            bucket=bucket,
            key=key,
            version_id=version_id,
            boto3_client=boto3_client,
            **sdk_options,
        )

        # Stores the list of data transformations
        self._data_transformations: List[BaseTransform] = []
        if is_gzip:
            self._data_transformations.append(GzipTransform())
        if is_csv:
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
            # Create a stream which is the result of applying all the data transformations

            # To start with, our transformed stream is the same as our raw seekable stream.
            # This means that if there are no data transformations to be applied, IO is just
            # delegated directly to the raw_stream.
            transformed_stream = self.raw_stream

            # Now we apply each transformation in order
            # e.g: when self._data_transformations is [transform_1, transform_2], then
            # transformed_stream is the equivalent of doing transform_2(transform_1(...(raw_stream)))
            for transformation in self._data_transformations:
                transformed_stream = transformation.transform(transformed_stream)

            self._transformed_stream = transformed_stream

        return self._transformed_stream

    @overload
    def transform(self, transformations: BaseTransform[T] | Sequence[BaseTransform[T]], in_place: Literal[True]) -> T:
        pass

    @overload
    def transform(
        self,
        transformations: BaseTransform[T] | Sequence[BaseTransform[T]],
        in_place: Literal[False],
    ) -> None:
        pass

    @overload
    def transform(self, transformations: BaseTransform[T] | Sequence[BaseTransform[T]]) -> T:
        pass

    def transform(
        self,
        transformations: BaseTransform[T] | Sequence[BaseTransform[T]],
        in_place: Optional[bool] = False,
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
        # Make transformations always be a sequence to make mypy happy
        if not isinstance(transformations, Sequence):
            transformations = [transformations]

        # Scenario 1: user wants to transform the stream in place.
        # In this case, we store the transformations and invalidate any existing transformed stream.
        # This way, the transformed_stream is re-created on the next IO operation.
        # This can happen when the user calls .transform multiple times before they start reading data
        #
        #   >>> s3object.transform(GzipTransform(), in_place=True)
        #   >>> s3object.seek(0, io.SEEK_SET) <- this creates a transformed stream
        #   >>> s3object.transform(CsvTransform(), in_place=True) <- need to re-create transformed stream
        #   >>> s3object.read...
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
        # Scenario 1: S3Object = SeekableIO, because there are no data transformations applied
        # In this scenario, we can only close the raw_stream. If we tried to also close the transformed_stream we would
        # get an error, since they are the same object, and we can't close the same stream twice.
        self.raw_stream.close()

        # Scenario 2: S3Object -> [Transformations] -> SeekableIO, because there are data transformations applied
        # In this scenario, we also need to close the transformed_stream if it exists. The reason we test for
        # existence is that the user might want to close the object without reading data from it. Example:
        #
        #   >>> s3object = S3Object(...., is_gzip=True)
        #   >>> s3object.close() <- transformed_stream doesn't exist yet at this point
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

    def write(self, data: Union[bytes, Union[bytearray, memoryview, Sequence[Any], "mmap", "_CData"]]) -> int:
        raise NotImplementedError("this stream is not writable")

    def writelines(
        self,
        data: Iterable[Union[bytes, Union[bytearray, memoryview, Sequence[Any], "mmap", "_CData"]]],
    ) -> None:
        raise NotImplementedError("this stream is not writable")
