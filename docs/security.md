---
title: Security
description: Security practices and processes for Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD041 MD043 -->

## Overview

[![Open Source Security Foundation Best Practices](https://bestpractices.coreinfrastructure.org/projects/7535/badge)](https://bestpractices.coreinfrastructure.org/projects/7535)

This page describes our security processes and supply chain practices.

!!! info "We continuously check and evolve our practices, therefore it is possible some diagrams may be eventually consistent."

--8<-- "SECURITY.md"

## Supply chain

### Verifying signed builds

!!! note "Starting from v2.20.0 releases, builds are [reproducible](https://slsa.dev/spec/v0.1/faq#q-what-about-reproducible-builds){target="_blank" rel="nofollow"} and signed publicly."

<center>
![SLSA Supply Chain Threats](https://slsa.dev/images/v1.0/supply-chain-threats.svg)

<i>Supply Chain Threats visualized by SLSA</i>
</center>

#### Terminology

We use [SLSA](https://slsa.dev/spec/v1.0/about){target="_blank" rel="nofollow"} to ensure our builds are reproducible and to adhere to [supply chain security practices](https://slsa.dev/spec/v1.0/threats-overview).

Within our [releases page](https://github.com/aws-powertools/powertools-lambda-python/releases), you will notice a new metadata file: `multiple.intoto.jsonl`. It's metadata to describe **where**, **when**, and **how** our build artifacts were produced - or simply, **attestation** in SLSA terminology.

For this to be useful, we need a **verification tool** - [SLSA Verifier](https://github.com/slsa-framework/slsa-verifier). SLSA Verifier decodes attestation to confirm the authenticity, identity, and the steps we took in our release pipeline (_e.g., inputs, git commit/branch, GitHub org/repo, build SHA256, etc._).

#### HOWTO

You can do this manually or automated via a shell script. We maintain the latter to ease adoption in CI systems (feel free to modify to your needs).

=== "Manually"

    * Download [SLSA Verifier binary](https://github.com/slsa-framework/slsa-verifier#download-the-binary)
    * Download the [latest release artifact from PyPi](https://pypi.org/project/aws-lambda-powertools/#files) (either wheel or tar.gz )
    * Download `multiple.intoto.jsonl` attestation from the [latest release](https://github.com/aws-powertools/powertools-lambda-python/releases/latest) under _Assets_

    !!! note "Next steps assume macOS as the operating system, and release v2.20.0"

    You should have the following files in the current directory:

    * **SLSA Verifier tool**: `slsa-verifier-darwin-arm64`
    * **Powertools Release artifact**: `aws_lambda_powertools-2.20.0-py3-none-any.whl`
    * **Powertools attestation**: `multiple.intoto.jsonl`

    You can now run SLSA Verifier with the following options:

    ```bash
    ./slsa-verifier-darwin-arm64 verify-artifact \
        --provenance-path "multiple.intoto.jsonl" \
        --source-uri github.com/aws-powertools/powertools-lambda-python \
        aws_lambda_powertools-2.20.0-py3-none-any.whl
    ```

=== "Automated"

    ```shell title="Verifying a release with verify_provenance.sh script"
    bash verify_provenance.sh 2.20.0
    ```

    !!! question "Wait, what does this script do?"

    I'm glad you asked! It takes the following actions:

    1. **Downloads SLSA Verifier** using the pinned version (_e.g., 2.3.0)
    2. **Verifies the integrity** of our newly downloaded SLSA Verifier tool
    3. **Downloads attestation** file for the given release version
    4. **Downloads `aws-lambda-powertools`** release artifact from PyPi for the given release version
    5. **Runs SLSA Verifier against attestation**, GitHub Source, and release binary
    6. **Cleanup** by removing downloaded files to keep your current directory tidy

    ??? info "Expand or [click here](https://github.com/aws-powertools/powertools-lambda-python/blob/develop/.github/actions/verify-provenance/verify_provenance.sh){target="_blank"} to see the script source code"

          ```bash title=".github/actions/verify-provenance/verify_provenance.sh"
          ---8<-- ".github/actions/verify-provenance/verify_provenance.sh"
          ```

<!-- markdownlint-disable MD013 -->
