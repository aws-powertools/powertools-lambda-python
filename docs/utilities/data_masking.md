---
title: Data Masking
description: Utility
---

<!-- markdownlint-disable MD051 -->

The data masking utility provides a simple solution to conceal incoming data so that sensitive information is not passed downstream or logged.


## Key features

* Mask data irreversibly without having to install any encryption library.
* Out of the box integration with AWS Encryption SDK to easily encrypt and decrypt data.
* Install any encryption provider and connect it with our new Data Masker class to easily mask, encrypt, and decrypt data.


## Terminology

Mask: This refers to concealing or partially replacing sensitive information with a non-sensitive placeholder or mask. The key characteristic of this operation is that it is irreversible, meaning the original sensitive data cannot be retrieved from the masked data. Masking is commonly applied when displaying data to users or for anonymizing data in non-reversible scenarios.

Encrypt: This is the process of transforming plaintext data into a ciphertext format using an encryption algorithm and a cryptographic key. Encryption is a reversible process, meaning the original data can be retrieved (decrypted) using the appropriate decryption key.

Decrypt: This is the process of reversing the encryption process, converting ciphertext back into plaintext using a decryption algorithm and the correct decryption key. Decryption is applied to recover the original data from its encrypted form. Decryption requires an encryption key that only authorized users have.

## Getting started

### IAM Permissions

If using the AWS Encryption SDK, your Lambda function IAM Role must have `kms:Encrypt`,  `kms:Decrypt` and `kms:GenerateDataKey` IAM permissions.

If using any other encryption provider, make sure to have the permissions for your role that it requires.

If not using any encryption services and just masking data, your Lambda does not need any additional permissions to use this utility.


### Required resources

If using the AWS Encryption SDK, you must have a KMS key with Encrypt, Decrypt, and GenerateDataKey permissions. 

If using any other encryption provider, you must have the resources required for that provider.


### Masking data
You can mask data without having to install any encryption library.

=== "getting_started_mask_data.py"
    ```python hl_lines="3 10"
    --8<-- "examples/data_masking/src/getting_started_mask_data.py"
    ```

### Encryting and decrypting data
In order to encrypt data, you must use either our out-of-the-box integration with the AWS Encryption SDK, or install another encryption provider of your own. You can still use the masking feature while using any encryption provider.

=== "getting_started_encrypt_data.py"
    ```python hl_lines="3 10"
    --8<-- "examples/data_masking/src/getting_started_encrypt_data.py"
    ```

## Advanced

### Adjusting configurations for AWS Encryption SDK

### Create your own encryption provider

You can create your own custom encryption provider by inheriting the `BaseProvider` class, and implementing both the `encrypt()` and `decrypt()` methods in order to encrypt and decrypt data using your custom encryption provider. You can also either use your own data serializer and deserializer by passing the `BaseProvider` class a `json_serializer` and `json_deserializer` argument, or you can use the default.

All masking logic is handled by the `mask()` and methods from the `BaseProvider` class.

Here is an examples of implementing a custom encryption using an external encryption library like [ItsDangerous](https://itsdangerous.palletsprojects.com/en/2.1.x/){target="_blank" rel="nofollow"}, a widely popular encryption library.

=== "working_with_own_provider.py"
    ```python hl_lines="5 13 20 24"
    --8<-- "examples/data_masking/src/working_with_own_provider.py"
    ```

=== "custom_provider.py"
    ```python hl_lines="6 9 17 24"
    --8<-- "examples/data_masking/src/custom_provider.py"
    ```

## Testing your code

For unit testing your applications, you can mock the calls to the data masking utility to avoid calling AWS APIs. This can be achieved in a number of ways - in this example, we use the pytest monkeypatch fixture to patch the `data_masking.encrypt` method.

=== "test_single_mock.py"
    ```python hl_lines="4 8"
    --8<-- "examples/data_masking/tests/test_single_mock.py"
    ```

=== "single_mock.py"
    ```python
    --8<-- "examples/data_masking/tests/src/single_mock.py"
    ```

If we need to use this pattern across multiple tests, we can avoid repetition by refactoring to use our own pytest fixture:

=== "test_with_fixture.py"
    ```python hl_lines="5 10"
    --8<-- "examples/data_masking/tests/test_with_fixture.py"
    ```