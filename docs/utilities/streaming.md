---
title: Streaming
description: Utility
---

The streaming utility handles datasets larger than the available memory as streaming data.

## Key Features

* Stream Amazon S3 objects with a file-like interface with minimal memory consumption
* Built-in popular data transformations to decompress and deserialize (gzip, CSV, and ZIP)
* Build your own data transformation and add it to the pipeline

## Background

Within Lambda, processing S3 objects larger than the allocated amount of memory can lead to out of memory or timeout situations. For cost efficiency, your S3 objects may be encoded and compressed in various formats (_gzip, CSV, zip files, etc_), increasing the  amount of non-business logic and reliability risks.

Streaming utility makes this process easier by fetching parts of your data as you consume it, and transparently applying data transformations to the data stream. This allows you to process one, a few, or all rows of your large dataset while consuming a few MBs only.

## Getting started

### Streaming from a S3 object

With `S3Object`, you'll need the bucket, object key, and optionally a version ID to stream its content.

We will fetch parts of your data from S3 as you process each line, consuming only the absolute minimal amount of memory.

=== "Non-versioned bucket"

    ```python hl_lines="8 9"
    --8<-- "examples/streaming/src/s3_basic_stream.py"
    ```

=== "Versioned bucket"

    ```python hl_lines="8 9"
    --8<-- "examples/streaming/src/s3_basic_stream_with_version.py"
    ```

### Data transformations

!!! tip "Think of data transformations like a data processing pipeline - apply one or more in order."

As data is streamed, you can apply transformations to your data like decompressing gzip content and deserializing a CSV into a dictionary.

For popular data transformations like CSV or Gzip, you can quickly enable it at the constructor level:

=== "Decompressing and deserializing CSV"

    ```python hl_lines="8"
    --8<-- "examples/streaming/src/s3_transform_common.py"
    ```

Alternatively, you can apply transformations later via the `transform` method. By default, it will return the transformed stream you can use to read its contents. If you prefer in-place modifications, use `in_place=True`.

???+ question "When is this useful?"
    In scenarios where you might have a reusable logic to apply common transformations. This might be a function or a class that receives an instance of `S3Object`.

=== "Returning a new object"

    ```python hl_lines="13"
    --8<-- "examples/streaming/src/s3_transform.py"
    ```

=== "Transform in-place"

    Note that when using `in_place=True`, there is no return (`None`).

    ```python hl_lines="13"
    --8<-- "examples/streaming/src/s3_transform_in_place.py"
    ```

#### Handling ZIP files

!!! warning "`ZipTransform` doesn't support combining other transformations."
    This is because a Zip file contains multiple files while transformations apply to a single stream.

That said, you can still open a specific file as a stream, reading only the necessary bytes to extract it:

```python hl_lines="6" title="Reading an individual file in the zip as a stream"
--8<-- "examples/streaming/src/s3_transform_zipfile.py"
```

#### Built-in data transformations

We provide popular built-in transformations that you can apply against your streaming data.

| Name     | Description                                                                                      | Class name    |
| -------- | ------------------------------------------------------------------------------------------------ | ------------- |
| **Gzip** | Gunzips the stream of data using the [gzip library](https://docs.python.org/3/library/gzip.html) | GzipTransform |
| **Zip**  | Exposes the stream as a [ZipFile object](https://docs.python.org/3/library/zipfile.html)         | ZipTransform  |
| **CSV**  | Parses each CSV line as a CSV object, returning dictionary objects                               | CsvTransform  |

## Advanced

### Custom options for data transformations

We will propagate additional options to the underlying implementation for each transform class.

| Name              | Available options                                                                     |
| ----------------- | ------------------------------------------------------------------------------------- |
| **GzipTransform** | [GzipFile constructor](https://docs.python.org/3/library/gzip.html#gzip.GzipFile)     |
| **ZipTransform**  | [ZipFile constructor](https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile) |
| **CsvTransform**  | [DictReader constructor](https://docs.python.org/3/library/csv.html#csv.DictReader)   |

For instance, take `ZipTransform`. You can use the `compression` parameter if you want to unzip an S3 object compressed with `LZMA`.

=== "Unzipping LZMA data"

    ```python hl_lines="12"
    --8<-- "examples/streaming/src/s3_transform_lzma.py"
    ```

Or, if you want to load a tab-separated file (TSV), you can use the `delimiter` parameter in the `CsvTransform`:

=== "Deserializing tab-separated data values"

    ```python hl_lines="11"
    --8<-- "examples/streaming/src/s3_transform_tsv.py"
    ```

### Building your own data transformation

You can build your own custom data transformation by extending the `BaseTransform` class. The `transform` method receives an `IO[bytes]` object, and you are responsible for returning an `IO[bytes]` object.

=== "Custom JSON transform"

    ```python hl_lines="10 12 27-29"
    --8<-- "examples/streaming/src/s3_json_transform.py"
    ```

## Testing your code

### Testing that you transformation is applied

Test that your transformation pipeline is returning the correct object:

=== "Testing the data pipeline returned object"

    ```python hl_lines="14 17"
    --8<-- "examples/streaming/src/test_s3_pipeline_result.py"
    ```

### Testing that your transformation is working in isolation

Create an input payload using `io.BytesIO` and assert the response of the transformation:

=== "Testing transformation in isolation"

    ```python hl_lines="23-25"
    --8<-- "examples/streaming/src/test_s3_transform_isolated.py"
    ```

### Testing that your transformation is working with S3 data

Use `botocore.stub` to stub the `get_object` response from S3:

=== "Testing transformation with mocked S3 data"

    ```python hl_lines="32-34 37"
    --8<-- "examples/streaming/src/test_s3_transform_mocked.py"
    ```
