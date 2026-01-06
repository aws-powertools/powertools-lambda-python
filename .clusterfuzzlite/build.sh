#!/bin/bash -eu

# Build fuzz targets from tests/fuzz/
for fuzzer in $(find $SRC/powertools/tests/fuzz -name 'fuzz_*.py'); do
    compile_python_fuzzer "$fuzzer"
done
