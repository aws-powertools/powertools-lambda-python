<!-- markdownlint-disable MD041 MD043 -->
# Architecture decision records

Premises of the project that are not visible in the code and that we found ourselves explaining more than once in reviews. They complement the [tenets](https://docs.powertools.aws.dev/lambda/python/latest/#tenets): tenets say what goes into the product, these say how we build it.

Each record is one page: context, decision, consequences, and what it means when you review or write a change. Records are not edited once accepted; a new record supersedes an old one and the old one points forward.

| ID | Title | Status |
| --- | --- | --- |
| [0001](0001-lambda-first.md) | Lambda first | Accepted |
| [0002](0002-every-millisecond-counts.md) | Every millisecond counts | Accepted |
| [0003](0003-python-versions.md) | Python versions follow the Lambda runtimes | Accepted |
| [0004](0004-layer-and-packaging.md) | Layer and packaging | Accepted |
| [0005](0005-tests-are-a-contract.md) | Tests are a contract | Accepted |
| [0006](0006-zero-regression-and-compatibility.md) | Zero regression and backwards compatibility | Accepted |
| [0007](0007-lean-dependencies.md) | Lean dependencies | Accepted |

## Adding a record

Copy the shape of an existing file, take the next number, and open a PR. A record is worth writing when a maintainer had to explain the same decision twice. Keep it to one page; link to the PRs or issues where the decision was made.
