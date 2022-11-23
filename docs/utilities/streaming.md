---
title: Streaming
description: Utility
---

The streaming utility handles streaming data from AWS for processing data sets bigger than the available memory.

## Key Features

* Simple interface to stream data from S3, even when the data is larger than memory
* Read your S3 file using the patterns you already know when dealing with files in Python
* Includes common transformations to data stored in S3, like gunzip and CSV deserialization
* Build your own data transformation and add it to the pipeline

## Background

Processing S3 files inside your Lambda function presents challenges when the file is bigger than the allocated
amount of memory. Your data may also be stored using a set of encapsulation layers (gzip, CSV, zip files, etc).

This utility makes it easy to process data coming from S3 files, while transparently applying data transformations
to the data stream.

## Getting started

### Streaming from a S3 object

To stream an S3 file, you need the bucket name, the key and optionally a version ID.

=== "Non-versioned bucket"

    ```python hl_lines="8 9"
    --8<-- "examples/streaming/src/s3_basic_stream.py"
    ```

=== "Versioned bucket"

    ```python hl_lines="8 9"
    --8<-- "examples/streaming/src/s3_basic_stream_with_version.py"
    ```

The code above will stream the contents from S3 as fast as possible, using minimal memory.

### Data transformations

The utility has some built-in data transformations to help dealing with common scenarios while streaming data from S3.

| Name     | Description                                                                                      | Class name    |
|----------|--------------------------------------------------------------------------------------------------|---------------|
| **Gzip** | Gunzips the stream of data using the [gzip library](https://docs.python.org/3/library/gzip.html) | GzipTransform |
| **Zip**  | Exposes the stream as a [ZipFile object](https://docs.python.org/3/library/zipfile.html)         | ZipTransform  |
| **CSV**  | Parses each line as a CSV object, returning dictionary objects                                   | CsvTransform  |

Common options like processing a gzipped stream or parsing data as CSV can be enabled directly on the constructor:

=== "Enabling inflation of gzip data"

    ```python hl_lines="8"
    --8<-- "examples/streaming/src/s3_transform_common.py"
    ```

Additionally, you can return a new object that encapsulates a transformation, or transform the data in place, by calling
the `transform` method. Multiple transformations are applied in order.

=== "Returning a new object"

    ```python hl_lines="13"
    --8<-- "examples/streaming/src/s3_transform.py"
    ```

=== "Transform in-place"

    ```python hl_lines="13"
    --8<-- "examples/streaming/src/s3_transform_in_place.py"
    ```

???+ note "Handling ZIP files with ZipTransformation"

    Currently, it's not possible to pipe the `ZipTransformation` into another data transformation,
    since a Zip file contains multiple files, and not a single stream. However, you can still
    open a specific file as a stream, reading only the necessary bytes to extract it:

    ```python hl_lines="6"
    --8<-- "examples/streaming/src/s3_transform_zipfile.py"
    ```

## Advanced

### Custom options for data transformations

Each data transformation class accepts additional options to customize the transformation.

| Name              | Description                                                                                                    |
|-------------------|----------------------------------------------------------------------------------------------------------------|
| **GzipTransform** | All the options from the [GzipFile constructor](https://docs.python.org/3/library/gzip.html#gzip.GzipFile)     |
| **ZipTransform**  | All the options from the [ZipFile constructor](https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile) |
| **CsvTransform**  | All the options from the [DictReader constructor](https://docs.python.org/3/library/csv.html#csv.DictReader)   |

For instance, if you want to unzip an S3 file compressed using `LZMA` you could pass that option in the constructor:

=== "Unzipping LZMA data"

    ```python hl_lines="12"
    --8<-- "examples/streaming/src/s3_transform_lzma.py"
    ```

Or, if you want to load a `TSV` file, you can just change the delimiter on the `CSV` transform:

=== "Loading TSV data"

    ```python hl_lines="11"
    --8<-- "examples/streaming/src/s3_transform_tsv.py"
    ```

### Building your own data transformation

You can build your own custom data transformation by extending the `BaseTransform` class.
The `transform` method receives an `IO[bytes]` object, and you are responsible for returning an object that is also
a `IO[bytes]`.

=== "Custom JSON transform"

    ```python hl_lines="10 12 27-29"
    --8<-- "examples/streaming/src/s3_json_transform.py"
    ```

## Testing your code

TODO
