---
title: Writing unit tests
description: Contributing unit tests to Powertools for AWS Lambda (Python)
---

### Testing definition

We group tests in different categories

| Test              | When to write                                                                                         | Notes                                                                                                                           | Speed                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Unit tests        | Verify the smallest possible unit works.                                                              | Networking access is prohibited. Prefer Functional tests given our complexity.                                                  | Lightning fast (nsec to ms)                       |
| Functional tests  | Guarantee functionality works as expected. It's a subset of integration test covering multiple units. | No external dependency. Prefer Fake implementations (in-memory) over Mocks and Stubs.                                           | Fast (ms to few seconds at worst)                 |
| Integration tests | Gain confidence that code works with one or more external dependencies.                               | No need for a Lambda function. Use our code base against an external dependency _e.g., fetch an existing SSM parameter_.        | Moderate to slow (a few minutes)                  |
| End-to-end tests  | Gain confidence that a Lambda function with our code operates as expected.                            | It simulates how customers configure, deploy, and run their Lambda function - Event Source configuration, IAM permissions, etc. | Slow (minutes)                                    |
| Performance tests | Ensure critical operations won't increase latency and costs to customers.                             | CI arbitrary hardware can make it flaky. We'll resume writing perf test after our new Integ/End have significant coverage.      | Fast to moderate (a few seconds to a few minutes) |

**NOTE**: Functional tests are mandatory. We have plans to create a guide on how to create these different tests. Maintainers will help indicate whether additional tests are necessary and provide assistance as required.
