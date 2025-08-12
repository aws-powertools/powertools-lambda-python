#!/bin/bash
# Error message:
# ImportError: libffi.so.6: cannot open shared object file

# Check library dependencies
ldd /opt/python/lib/python3.11/site-packages/some_package/_extension.so

# Solution: Use Lambda base image with system dependencies
# Or switch to pure Python alternatives
