#!/bin/sh

al2_versions=("3.9" "3.10" "3.11")

# Flag to indicate if the version is al2 or not
is_al2=0

for version in "${al2_versions[@]}"; do
    if [ "$PYTHON_VERSION" = "$version" ]; then
        is_al2=1
        break
    fi
done

if [ "$is_al2" -eq 1 ]; then
     yum update -y && yum install -y zip unzip wget tar gzip binutils
     yum install -y \
        boost-devel \
        jemalloc-devel \
        bison \
        make \
        gcc \
        gcc-c++ \
        flex \
        autoconf \
        zip \
        git \
        ninja-build

else
    dnf update -y && dnf install -y zip unzip wget tar gzip binutils
    dnf install -y \
        boost-devel \
        jemalloc-devel \
        bison \
        make \
        gcc \
        gcc-c++ \
        flex \
        autoconf \
        zip \
        git \
        ninja-build

fi
