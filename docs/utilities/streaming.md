---
title: Streaming
description: Utility
---

The streaming utility handles streaming data from AWS for processing data sets bigger than the available memory.

## Key Features

* Simple interface to stream data from S3, even when the data is larger than memory
* Read your S3 file using the patterns you already know to deal with files in Python
* Includes common transformations to data stored in S3, like Gzip and Json deserialization
* Build your own data transformation and add it to the pipeline

## Background

Processing S3 files inside your Lambda function presents challenges when the file is bigger than the allocated
amount of memory. Your data may also be stored using a set of encapsulation layers (gzip, JSON strings, etc).

This utility makes it easy to process data coming from S3 files, while applying data transformations transparently
to the data stream.

## Getting started

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

The utility has some built-in data transformations to help deal with common scenarios while streaming data from S3.

| Name     | Description                                                                                      |
|----------|--------------------------------------------------------------------------------------------------|
| **Gzip** | Gunzips the stream of data using the [gzip library](https://docs.python.org/3/library/gzip.html) |
| **Zip**  | Exposes the stream as a [ZipFile object](https://docs.python.org/3/library/zipfile.html)         |
| **CSV**  | Parses each line as a CSV object, returning dictionary objects                                   |

Common options like gunzipping a stream and parsing data as CSV can be enabled directly on the constructor:

```python hl_lines="8"
--8<-- "examples/streaming/src/s3_transform_common.py"
```

Additionally, you can transform the data in place, or return a new object that encapsulates the transformation.
Multiple transformations are applied in order.

=== "Returning a new object"

    ```python hl_lines="13"
    --8<-- "examples/streaming/src/s3_transform.py"
    ```

=== "Transform in-place"

    ```python hl_lines="13"
    --8<-- "examples/streaming/src/s3_transform_in_place.py"
    ```

## Advanced

### Custom options for data transformations

Each data transformation class accepts additional options to customize the transformation.

| Name     | Description                                                                                                    |
|----------|----------------------------------------------------------------------------------------------------------------|
| **Gzip** | All the options from the [GzipFile constructor](https://docs.python.org/3/library/gzip.html#gzip.GzipFile)     |
| **Zip**  | All the options from the [ZipFile constructor](https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile) |
| **CSV**  | All the options from the [DictReader constructor](https://docs.python.org/3/library/csv.html#csv.DictReader)   |

For instance, if you want to unzip an S3 file compressed using `LZMA` you could pass that option in the constructor:

```python hl_lines="12"
--8<-- "examples/streaming/src/s3_transform_lzma.py"
```

### Building your own data transformation

You can build your own custom data transformation by extending the `BaseTransform` class.
The `transform` method receives an `io.RawIOBase` object, and you are responsible for returning an object that is also
a `io.RawIOBase`.

```python hl_lines="9 37 38"
--8<-- "aws_lambda_powertools/utilities/streaming/transformations/json.py"
```

## Testing your code

TODO
