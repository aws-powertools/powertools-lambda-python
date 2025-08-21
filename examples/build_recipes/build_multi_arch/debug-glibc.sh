#!/bin/bash
# Error message:
# ImportError: /lib64/libc.so.6: version `GLIBC_2.34' not found

# Check GLIBC version in Lambda runtime
ldd --version

# Check required GLIBC symbols in a library
objdump -T /opt/python/lib/python3.11/site-packages/pydantic/_internal/_pydantic_core.so | grep GLIBC

# Solution: Rebuild with compatible base image
docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.11 \
    pip install --force-reinstall pydantic -t /var/task/
