import powertools_base64_gzip_jmespath_schema as schemas

from aws_lambda_powertools.utilities.validation import validate

sample_event = {
    "data": "H4sIACZAXl8C/52PzUrEMBhFX2UILpX8tPbHXWHqIOiq3Q1F0ubrWEiakqTWofTdTYYB0YWL2d5zvnuTFellBIOedoiyKH5M0iwnlKH7HZL6dDB6ngLDfLFYctUKjie9gHFaS/sAX1xNEq525QxwFXRGGMEkx4Th491rUZdV3YiIZ6Ljfd+lfSyAtZloacQgAkqSJCGhxM6t7cwwuUGPz4N0YKyvO6I9WDeMPMSo8Z4Ca/kJ6vMEYW5f1MX7W1lVxaG8vqX8hNFdjlc0iCBBSF4ERT/3Pl7RbMGMXF2KZMh/C+gDpNS7RRsp0OaRGzx0/t8e0jgmcczyLCWEePhni/23JWalzjdu0a3ZvgEaNLXeugEAAA=="  # noqa: E501
}

validate(event=sample_event, schema=schemas.INPUT, envelope="powertools_base64_gzip(data) | powertools_json(@)")
