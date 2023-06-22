---
title: Streaming
description: Utility
---

The streaming utility handles datasets larger than the available memory as streaming data.

## Key features

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

| Name     | Description                                                                                                       | Class name    |
| -------- | ----------------------------------------------------------------------------------------------------------------- | ------------- |
| **Gzip** | Gunzips the stream of data using the [gzip library](https://docs.python.org/3/library/gzip.html){target="_blank"} | GzipTransform |
| **Zip**  | Exposes the stream as a [ZipFile object](https://docs.python.org/3/library/zipfile.html){target="_blank"}         | ZipTransform  |
| **CSV**  | Parses each CSV line as a CSV object, returning dictionary objects                                                | CsvTransform  |

## Advanced

### Skipping or reading backwards

`S3Object` implements [Python I/O interface](https://docs.python.org/3/tutorial/inputoutput.html){target="_blank"}. This means you can use `seek` to start reading contents of your file from any particular position, saving you processing time.

#### Reading backwards

For example, let's imagine you have a large CSV file, each row has a non-uniform size (bytes), and you want to read and process the last row only.

```csv title="non_uniform_sample.csv"
--8<-- "examples/streaming/src/non_uniform_sample.csv"
```

You found out the last row has exactly 30 bytes. We can use `seek()` to skip to the end of the file, read 30 bytes, then transform to CSV.

```python title="Reading only the last CSV row" hl_lines="16 19"
--8<-- "examples/streaming/src/s3_csv_stream_non_uniform_seek.py"
```

#### Skipping

!!! question "What if we want to jump the first N rows?"

You can also solve with `seek`, but let's take a large uniform CSV file to make this easier to grasp.

```csv title="uniform_sample.csv"
--8<-- "examples/streaming/src/uniform_sample.csv"
```

You found out that each row has 8 bytes, the header line has 21 bytes, and every new line has 1 byte. You want to skip the first 100 lines.

```python hl_lines="28 31" title="Skipping the first 100 rows"
--8<-- "examples/streaming/src/s3_csv_stream_seek.py"
```

### Custom options for data transformations

We will propagate additional options to the underlying implementation for each transform class.

| Name              | Available options                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| **GzipTransform** | [GzipFile constructor](https://docs.python.org/3/library/gzip.html#gzip.GzipFile){target="_blank"}     |
| **ZipTransform**  | [ZipFile constructor](https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile){target="_blank"} |
| **CsvTransform**  | [DictReader constructor](https://docs.python.org/3/library/csv.html#csv.DictReader){target="_blank"}   |

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

### Asserting data transformations

Create an input payload using `io.BytesIO` and assert the response of the transformation:

=== "assert_transformation.py"

    ```python hl_lines="3 13 15 23-28 31-32"
    --8<-- "examples/streaming/src/assert_transformation.py"
    ```

=== "assert_transformation_module.py"

    ```python hl_lines="16"
    --8<-- "examples/streaming/src/assert_transformation_module.py"
    ```

## Known limitations

### AWS X-Ray segment size limit

We make multiple API calls to S3 as you read chunks from your S3 object. If your function is decorated with [Tracer](./../core/tracer.md){target="_blank"}, you can easily hit [AWS X-Ray 64K segment size](https://docs.aws.amazon.com/general/latest/gr/xray.html#limits_xray){target="_blank"} when processing large files.

!!! tip "Use tracer decorators in parts where you don't read your `S3Object` instead."
