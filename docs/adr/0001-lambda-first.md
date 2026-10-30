<!-- markdownlint-disable MD041 MD043 -->
# 0001. Lambda first

Status: Accepted

## Context

Powertools for AWS Lambda (Python) runs inside AWS Lambda. That execution model is specific: the service decides when an execution environment is created, reused, paused or recycled, how many invocations it handles and whether they run concurrently (as with Lambda Managed Instances), `/tmp` is the only writable disk, and any call may be a fresh cold start.

Code that works well in a long-running web server (background threads, connection pools warmed at import, periodic refresh timers, in-memory state that assumes to survive) behaves differently or breaks here.

The utilities also get used outside Lambda, in local development, tests, containers and sometimes in other frameworks. That usage is welcome but it is not what we design for.

## Decision

We design, test and optimise for the Lambda execution model only.

- A utility must be correct when the environment is paused right after the handler returns, when it never runs again, and when several invocations run in it at once.
- No background threads, timers or work that assumes the process stays alive after the invocation. Anything that must happen, happens inside the invocation.
- In-memory state (caches, counters, connections) is treated as per execution environment: it may be reused across invocations, it may vanish at any time, and it may be touched by concurrent invocations. Anything shared must be safe under that concurrency.
- Cold start is a first-class scenario. See [ADR 0002](0002-every-millisecond-counts.md).
- Behaviour outside Lambda is best effort. We do not add code paths for other runtimes, and we do not accept changes whose only benefit shows outside Lambda.

## Consequences

- Reviews ask "what happens on a cold start, and what happens if the environment is recycled right after this?" for every stateful change.
- Concurrency inside one environment comes from concurrent invocations, from the customer's own threads and from coroutines, so thread and coroutine safety is a requirement, not a nicety (see the circuit breaker's single-prober guarantee). Coordination across environments goes through AWS services, never shared memory.
- Features that need a long-lived process are declined or redesigned around an invocation boundary.

## When reviewing or writing a change

Ask where the state lives and who cleans it up. If the answer depends on the process surviving, it does not fit.
