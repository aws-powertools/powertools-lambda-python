from __future__ import annotations

import io

from avro.errors import SchemaResolutionException
from avro.io import BinaryDecoder, DatumReader


def deserialize_avro(avro_bytes, reader_schema: str | None = None):
    """
    Deserialize Avro binary data to Python objects

    Parameters
    ----------
    avro_bytes: bytes
        Avro binary data
    reader_schema: str, Optional
        Schema to use for reading

    Returns
    -------
    dict
        Deserialized Python object

    Raises
    ------
    ValueError
        If reader_schema schema is None or if deserialization fails
    """
    try:
        reader = DatumReader(reader_schema)

        decoder = BinaryDecoder(io.BytesIO(avro_bytes))
        return reader.read(decoder)
    except SchemaResolutionException as e:
        raise ValueError(f"Schema mismatch: {e}") from e
    except Exception as e:
        raise ValueError(f"Failed to deserialize Avro data: {e}") from e
