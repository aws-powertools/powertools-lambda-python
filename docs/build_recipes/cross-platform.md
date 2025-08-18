---
title: Cross-Platform Build Considerations
description: Handle architecture differences when building AWS Lambda packages
---

<!-- markdownlint-disable MD043 -->

Many modern Python packages include compiled extensions written in Rust or C/C++ for performance reasons. These compiled components are platform-specific and can cause deployment issues when building on different architectures.

???+ warning "Architecture Mismatch Issues"
    Building AWS Lambda packages on macOS (ARM64/Intel) for deployment on AWS Lambda (Linux x86_64 or ARM64) will result in incompatible binary dependencies that cause import errors at runtime.

## Common compiled libraries

Taking into consideration Powertools for AWS dependencies and common Python packages, these libraries include compiled Rust/C components that require architecture-specific builds:

| Library | Language | Components | Impact | Used in Powertools for AWS|
|---------|----------|------------|--------|-------------------|
| **pydantic** | Rust | Core validation engine | High - Core functionality affected | ✅ Core dependency |
| **aws-encryption-sdk** | C | Encryption/decryption | High - Data masking fails | ✅ Optional (datamasking extra) |
| **protobuf** | C++ | Protocol buffer serialization | High - Message parsing fails | ✅ Optional (kafka-consumer-protobuf) |
| **redis** | C | Redis client with hiredis | Medium - Falls back to pure Python | ✅ Optional (redis extra) |
| **valkey-glide** | Rust | High-performance Redis client | High - Client completely broken | ✅ Optional (valkey extra) |
| **orjson** | Rust | JSON serialization | Medium - Performance degradation | ❌ Not used (but common) |
| **uvloop** | C | Event loop implementation | Medium - Falls back to asyncio | ❌ Not used (but common) |
| **lxml** | C | XML/HTML processing | High - XML parsing fails | ❌ Not used (but common) |

## Powertools extras dependencies and architecture

Different Powertools for AWS extras dependencies have varying levels of architecture dependency:

=== "Safe extras (pure python)"

    ```txt title="requirements.txt - Safe for any platform"
    # The 'all' extra includes both safe and architecture-dependent packages
    aws-lambda-powertools[all]==3.18.0

    # This is equivalent to:
    # pydantic, pydantic-settings, aws-xray-sdk, fastjsonschema,
    # aws-encryption-sdk, jsonpath-ng
    ```

=== "Architecture-dependent extras"

    ```txt title="requirements.txt - Requires Linux builds"
    # These extras include compiled dependencies
    aws-lambda-powertools[parser]==3.18.0           # pydantic (Rust)
    aws-lambda-powertools[validation]==3.18.0       # fastjsonschema (C)
    aws-lambda-powertools[datamasking]==3.18.0      # aws-encryption-sdk (C)
    aws-lambda-powertools[redis]==3.18.0            # redis with hiredis (C)
    aws-lambda-powertools[valkey]==3.18.0           # valkey-glide (Rust)
    aws-lambda-powertools[kafka-consumer-avro]==3.18.0      # avro (C)
    aws-lambda-powertools[kafka-consumer-protobuf]==3.18.0  # protobuf (C++)
    ```

=== "All extras (mixed dependencies)"

    ```txt title="requirements.txt - Requires careful platform handling"
    # These extras have minimal or no compiled dependencies
    aws-lambda-powertools[tracer]==3.18.0      # aws-xray-sdk (mostly pure Python)
    aws-lambda-powertools[aws-sdk]==3.18.0    # boto3 (pure Python)

    ```

???+ tip "Powertools for AWS build strategy"
    1. **Use `[all]` extra with Docker builds** for maximum compatibility
    2. **Use specific extras** if you want to avoid certain compiled dependencies
    3. **Test imports** after building to catch architecture mismatches early

## Understanding Python wheels

Python wheels are binary distribution packages that include compiled extensions. Lambda requires specific wheel types based on the target runtime architecture and GLIBC version.

### Wheel naming convention

Wheels follow a specific naming pattern that indicates compatibility:

```txt
{package}-{version}-{python tag}-{abi tag}-{platform tag}.whl
```

**Example breakdown:**

```txt
pydantic-2.5.0-cp311-cp311-linux_x86_64.whl
│        │     │     │     └─ Platform: Linux x86_64
│        │     │     └─ ABI: CPython 3.11
│        │     └─ Python: CPython 3.11
│        └─ Version: 2.5.0
└─ Package: pydantic
```

### Platform tags and Lambda compatibility

| Platform Tag | Description | Lambda Compatibility |
|--------------|-------------|---------------------|
| `linux_x86_64` | Linux 64-bit Intel/AMD | ✅ Lambda x86_64 |
| `linux_aarch64` | Linux 64-bit ARM | ✅ Lambda arm64 |
| `macosx_*` | macOS (any version) | ❌ Not compatible |
| `win_*` | Windows (any version) | ❌ Not compatible |
| `any` | Pure Python, no compiled code | ✅ All platforms |

### Source distributions vs wheels

| Package Type | Extension | Compilation | Lambda Recommendation |
|--------------|-----------|-------------|----------------------|
| **Wheel** | `.whl` | Pre-compiled | ✅ Preferred - faster, consistent |
| **Source Distribution** | `.tar.gz` | Compile during install | ❌ Avoid - platform-dependent compilation |

**Why wheels matter for Lambda:**

* **Consistent builds** - Same binary across environments
* **Faster installs** - No compilation step required
* **Predictable dependencies** - Known system library requirements
* **Architecture safety** - Platform-specific binaries

## Lambda runtime environments

<!-- markdownlint-disable MD013 -->
Lambda managed runtimes use [specific Amazon Linux versions](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html#runtimes-supported) versions with fixed GLIBC versions. Packages built on development machines with newer GLIBC versions will fail at runtime with import errors. Each Python runtime version corresponds to a specific Amazon Linux base system that determines compatible system library versions.
<!-- markdownlint-enable MD013 -->

### Amazon Linux versions and GLIBC compatibility

| Python Runtime | Base System       | GLIBC Version | Architecture Support |
|----------------|-------------------|---------------|----------------------|
| **python3.9**  | Amazon Linux 2    | 2.26          | x86_64, arm64        |
| **python3.10** | Amazon Linux 2    | 2.26          | x86_64, arm64        |
| **python3.11** | Amazon Linux 2    | 2.26          | x86_64, arm64        |
| **python3.12** | Amazon Linux 2023 | 2.34          | x86_64, arm64        |
| **python3.13** | Amazon Linux 2023 | 2.34          | x86_64, arm64        |

???+ warning "GLIBC Version Mismatch"
    Compiled libraries built on systems with newer GLIBC versions will fail on Lambda runtimes with older GLIBC versions. Ubuntu 24.04 (GLIBC 2.39) and Ubuntu 22.04 (GLIBC 2.35) are incompatible with Lambda python3.11 and earlier (GLIBC 2.26). Always use `--platform` flags or Docker with Lambda base images.

### Manylinux compatibility tags

Python wheels use manylinux tags to indicate GLIBC compatibility. Understanding these tags helps you choose the right wheels for Lambda:

| manylinux Tag | GLIBC Version | Lambda Compatibility | Recommendation |
|---------------|---------------|---------------------|----------------|
| **manylinux1** | 2.5 | ✅ All runtimes | Legacy, limited package support |
| **manylinux2010** | 2.12 | ✅ All runtimes | Good compatibility |
| **manylinux2014** | 2.17 | ✅ All runtimes | Recommended for most packages |
| **manylinux_2_17** | 2.17 | ✅ All runtimes | Modern standard |
| **manylinux_2_24** | 2.24 | ✅ All runtimes | Good for newer packages |
| **manylinux_2_28** | 2.28 | ✅ python3.12+, ❌ python3.11- | Use with caution |
| **manylinux_2_34** | 2.34 | ✅ python3.12+, ❌ python3.11- | AL2023 only |

## Runtime-specific considerations

### Amazon Linux 2 (python3.8 - python3.11)

Amazon Linux 2 is based on RHEL 7 and uses an older GLIBC version (2.26). This provides broad compatibility but may limit access to newer compiled features.

**Characteristics:**

* **GLIBC 2.26** - Compatible with most manylinux wheels
* **OpenSSL 1.0.2** - Legacy TLS support

**Best practices:**

```bash
--8<-- "examples/build_recipes/build_multi_arch/build-al2.sh"
```

### Amazon Linux 2023 (python3.12+)

Amazon Linux 2023 is a modern, minimal Linux distribution with updated system libraries and better security.

**Characteristics:**

* **GLIBC 2.34** - Supports newer compiled libraries
* **OpenSSL 3.0** - Latest TLS and cryptographic features
* **Smaller footprint** - Optimized for containers and serverless

**Migration considerations:**

```bash
--8<-- "examples/build_recipes/build_multi_arch/build-al2023.sh"
```

## Multi-platform build strategies

=== "Docker-based Builds (Recommended)"

    Use AWS Lambda base images to ensure Linux x86_64 or ARM64 compatibility:

    === "Dockerfile"

        ```dockerfile
        --8<-- "examples/build_recipes/build_multi_arch/Dockerfile.lambda"
        ```

    === "Build Script"

        ```bash
        --8<-- "examples/build_recipes/build_multi_arch/build-multiplatform.sh"
        ```

=== "Platform-specific pip install"

    Force installation of Linux-compatible wheels:

    === "Build Script"

        ```bash
        --8<-- "examples/build_recipes/build_multi_arch/build-linux-wheels.sh"
        ```

=== "GitHub Actions multi-arch"

    Use GitHub Actions with Linux runners for consistent builds:

    === "Workflow"

        ```yaml
        --8<-- "examples/build_recipes/build_multi_arch/lambda-build.yml"
        ```

## Debugging compatibility issues

When you encounter runtime errors related to compiled dependencies, use these techniques to diagnose and fix the issues:

### Common error patterns

=== "GLIBC version errors"

    ```bash
    --8<-- "examples/build_recipes/build_multi_arch/debug-glibc.sh"
    ```

=== "Architecture mismatch"

    ```bash
    --8<-- "examples/build_recipes/build_multi_arch/debug-arch-mismatch.sh"
    ```

=== "Missing system libraries"

    ```bash
    --8<-- "examples/build_recipes/build_multi_arch/debug-missing-libs.sh"
    ```

## Best practices for cross-platform builds

???+ tip "Development Workflow"
    Develop locally on your preferred platform, but always build deployment packages in a Linux environment or Docker container to ensure compatibility.

1. **Always build on Linux** for Lambda deployments, or use Docker with Lambda base images
2. **Use `--platform` flags** when installing with pip to force Linux-compatible wheels
3. **Test imports** in your build environment before deployment
4. **Pin dependency versions** to ensure reproducible builds across platforms
5. **Use CI/CD with Linux runners** to avoid local architecture issues
6. **Consider Lambda container images** for complex dependency scenarios
