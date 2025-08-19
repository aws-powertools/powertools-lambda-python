#!/bin/bash
# Some packages may require rebuilding for AL2023
# Check for GLIBC symbol errors in logs:
# ImportError: /lib64/libc.so.6: version `GLIBC_2.34' not found

# Use AL2023 base image for python3.12+
docker run --rm -v "$PWD":/var/task \
    public.ecr.aws/lambda/python:3.12 \
    pip install -r requirements.txt -t /var/task/
