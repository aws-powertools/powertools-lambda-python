#!/bin/bash
# Error message:
# ImportError: cannot import name '_speedups' from 'pydantic'

# Check library architecture
file /opt/python/lib/python3.11/site-packages/pydantic/_internal/_pydantic_core.so

# Expected output for Lambda x86_64:
# ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked

# Solution: Force correct platform
pip install --platform manylinux2014_x86_64 --force-reinstall pydantic -t build/
