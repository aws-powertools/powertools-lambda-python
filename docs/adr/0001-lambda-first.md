<!-- markdownlint-disable MD041 MD043 -->
# 0001. Lambda first

Status: Accepted

## Context

Powertools runs inside AWS Lambda. That execution model is specific: one invocation at a time per execution environment, environments are frozen between invocations and recycled without notice, `/tmp` is the only writable disk, and the process may be a fresh cold start on any call.

Code that works well in a long-running web server (background threads, connection pools warmed at import, periodic refresh timers, in-memory state that assumes to survive) behaves differently or breaks here.

The utilities also get used outside Lambda, in local development, tests, containers and sometimes in other frameworks. That usage is welcome but it is not what we design for.

## Decision

We design, test and optimise for the Lambda execution model only.

- A utility must be correct when the environment is frozen right after the handler returns and when it never runs again.
- No background threads, timers or work that assumes the process stays alive after the invocation. Anything that must happen, happens inside the invocation.
- In-memory state (caches, counters, connections) is treated as per execution environment: it may be reused across invocations, it may vanish at any time, and it is never shared between concurrent invocations because Lambda does not run them in the same environment.
- Cold start is a first-class scenario. See [ADR 0002](0002-every-millisecond-counts.md).
- Behaviour outside Lambda is best effort. We do not add code paths for other runtimes, and we do not accept changes whose only benefit shows outside Lambda.

## Consequences

- Reviews ask "what happens on a cold start, and what happens if the environment is recycled right after this?" for every stateful change.
- Concurrency inside one environment comes from the customer's own threads or coroutines within a single invocation, so thread and coroutine safety still matter (see the circuit breaker's single-prober guarantee), but cross-process coordination goes through AWS services, not shared memory.
- Features that need a long-lived process are declined or redesigned around an invocation boundary.

## When reviewing or writing a change

Ask where the state lives and who cleans it up. If the answer depends on the process surviving, it does not fit.
