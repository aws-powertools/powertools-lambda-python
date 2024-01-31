#!/bin/bash
set -uo pipefail # prevent accessing unset env vars, prevent masking pipeline errors to the next command

#docs
#title              :verify_provenance.sh
#description        :This script will download and verify a signed Powertools for AWS Lambda (Python) release build with SLSA Verifier
#author		    :@heitorlessa
#date               :July 1st 2023
#version            :0.1
#usage		    :bash verify_provenance.sh {release version}
#notes              :Meant to use in GitHub Actions or locally (MacOS, Linux, WSL).
#os_version         :Ubuntu 22.04.2 LTS
#==============================================================================

# Check if RELEASE_VERSION is provided as a command line argument
if [[ $# -eq 1 ]]; then
    export readonly RELEASE_VERSION="$1"
else
    echo "ERROR: Please provider Powertools release version as a command line argument."
    echo "Example: bash verify_provenance.sh 2.20.0"
    exit 1
fi

export readonly ARCHITECTURE=$(uname -m | sed 's/x86_64/amd64/g') # arm64, x86_64 ->amd64
export readonly OS_NAME=$(uname -s | tr '[:upper:]' '[:lower:]')  # darwin, linux
export readonly SLSA_VERIFIER_VERSION="2.3.0"
export readonly SLSA_VERIFIER_CHECKSUM_FILE="SHA256SUM.md"
export readonly SLSA_VERIFIER_BINARY="./slsa-verifier-${OS_NAME}-${ARCHITECTURE}"

export readonly RELEASE_BINARY="aws_lambda_powertools-${RELEASE_VERSION}-py3-none-any.whl"
export readonly ORG="aws-powertools"
export readonly REPO="powertools-lambda-python"
export readonly PROVENANCE_FILE="multiple.intoto.jsonl"

export readonly FILES=("${SLSA_VERIFIER_BINARY}" "${SLSA_VERIFIER_CHECKSUM_FILE}" "${PROVENANCE_FILE}" "${RELEASE_BINARY}")

function debug() {
    TIMESTAMP=$(date -u "+%FT%TZ") # 2023-05-10T07:53:59Z
    echo ""${TIMESTAMP}" DEBUG - [*] $1"
}

function error() {
    cleanup
    TIMESTAMP=$(date -u "+%FT%TZ") # 2023-05-10T07:53:59Z
    echo ""${TIMESTAMP}" ERROR - [!] $1"
    echo ""${TIMESTAMP}" ERROR - [!] exiting"
    exit 1
}

function download_slsa_verifier() {
    readonly SLSA_URL="https://github.com/slsa-framework/slsa-verifier/releases/download/v${SLSA_VERIFIER_VERSION}/slsa-verifier-${OS_NAME}-${ARCHITECTURE}"
    # debug "Downloading SLSA Verifier for - Binary: slsa-verifier-${OS_NAME}-${ARCHITECTURE}"
    debug "Downloading SLSA Verifier binary: ${SLSA_URL}"
    curl \
        --location \
        --fail \
        --silent \
        -O "${SLSA_URL}" || error "Failed to download SLSA Verifier binary"

    readonly SLSA_CHECKSUM_URL="https://raw.githubusercontent.com/slsa-framework/slsa-verifier/f59b55ef2190581d40fc1a5f3b7a51cab2f4a652/${SLSA_VERIFIER_CHECKSUM_FILE}"
    debug "Downloading SLSA Verifier checksums"
    curl \
        --location \
        --fail \
        --silent \
        -O "${SLSA_CHECKSUM_URL}" || error "Failed to download SLSA Verifier binary checksum file"

    debug "Verifying SLSA Verifier binary integrity"
    CURRENT_HASH=$(sha256sum "${SLSA_VERIFIER_BINARY}" | awk '{print $1}')
    if [[ $(grep "${CURRENT_HASH}" "${SLSA_VERIFIER_CHECKSUM_FILE}") ]]; then
        debug "SLSA Verifier binary integrity confirmed"
        chmod +x "${SLSA_VERIFIER_BINARY}"
    else
        error "Failed integrity check for SLSA Verifier binary: ${SLSA_VERIFIER_BINARY}"
    fi
}

function download_provenance() {
    readonly PROVENANCE_URL="https://github.com/${ORG}/${REPO}/releases/download/v${RELEASE_VERSION}/${PROVENANCE_FILE}"
    debug "Downloading attestation: ${PROVENANCE_URL}"

    curl \
        --location \
        --fail \
        --silent \
        -O ${PROVENANCE_URL} || error "Failed to download provenance. Does the release already exist?"
}

function download_release_artifact() {
    debug "Downloading ${RELEASE_VERSION} release from PyPi"
    python -m pip download \
        --only-binary=:all: \
        --no-deps \
        --quiet \
        aws-lambda-powertools=="${RELEASE_VERSION}"
}

function verify_provenance() {
    debug "Verifying attestation with slsa-verifier"
    "${SLSA_VERIFIER_BINARY}" verify-artifact \
        --provenance-path "${PROVENANCE_FILE}" \
        --source-uri github.com/${ORG}/${REPO} \
        ${RELEASE_BINARY}
}

function cleanup() {
    debug "Cleaning up previously downloaded files"
    rm -f "${SLSA_VERIFIER_BINARY}"
    rm -f "${SLSA_VERIFIER_CHECKSUM_FILE}"
    rm -f "${PROVENANCE_FILE}"
    rm -f "${RELEASE_BINARY}"
    echo "${FILES[@]}" | xargs -n1 echo "Removed file: "
}

function main() {
    download_slsa_verifier
    download_provenance
    download_release_artifact
    verify_provenance
    cleanup
}

main

# Lessons learned
#
# 1. If source doesn't match provenance
#
# FAILED: SLSA verification failed: source used to generate the binary does not match provenance: expected source 'awslabs/aws-lambda-powertools-python', got 'heitorlessa/aws-lambda-powertools-test'
#
# 2. Avoid building deps during download in Test registry endpoints
#
# FAILED: Could not find a version that satisfies the requirement poetry-core>=1.3.2 (from versions: 1.2.0)
#
