#!/bin/bash
set -e -x

# Install a system package required by our library
yum install -y atlas-devel

VERSIONS=(cp36-cp36m cp37-cp37m cp38-cp38)

# Compile wheels
for VERSION in ${VERSIONS[@]}; do
    "/opt/python/${VERSION}/bin/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done

# Install package using built wheels across all version
for VERSION in ${VERSIONS[@]}; do
    echo "Installing ------ ${VERSION}"
    "/opt/python/${VERSION}/bin/pip" install aws_lambda_powertools --no-index -f /io/wheelhouse
done
