---
title: Middleware factory
description: Utility
---

Middleware factory provides a decorator factory to create your own middleware to run logic before, and after each Lambda invocation synchronously.

## Key features

* Run logic before, after, and handle exceptions
* Trace each middleware when requested

## Middleware with no params

You can create your own middleware using `lambda_handler_decorator`. The decorator factory expects 3 arguments in your function signature:

* **handler** - Lambda function handler
* **event** - Lambda function invocation event
* **context** - Lambda function context object

```python hl_lines="4-5 12" title="Creating your own middleware for before/after logic"
--8<-- "docs/examples/utilities/middleware_factory/middleware_no_params.py"
```

## Middleware with params

You can also have your own keyword arguments after the mandatory arguments.

```python hl_lines="7 17" title="Accepting arbitrary keyword arguments"
--8<-- "docs/examples/utilities/middleware_factory/middleware_with_params.py"
```

## Tracing middleware execution

If you are making use of [Tracer](../core/tracer.md), you can trace the execution of your middleware to ease operations.

This makes use of an existing Tracer instance that you may have initialized anywhere in your code.

```python hl_lines="4" title="Tracing custom middlewares with Tracer"
--8<-- "docs/examples/utilities/middleware_factory/middleware_trace_execution.py"
```

When executed, your middleware name will [appear in AWS X-Ray Trace details as](../core/tracer.md) `## middleware_name`.

For advanced use cases, you can instantiate [Tracer](../core/tracer.md) inside your middleware, and add annotations as well as metadata for additional operational insights.

```python hl_lines="7-9" title="Add custom tracing insights before/after in your middlware"
--8<-- "docs/examples/utilities/middleware_factory/middleware_trace_custom.py"
```

## Tips

* Use `trace_execution` to quickly understand the performance impact of your middlewares, and reduce or merge tasks when necessary
* When nesting multiple middlewares, always return the handler with event and context, or response
* Keep in mind [Python decorators execution order](https://realpython.com/primer-on-python-decorators/#nesting-decorators){target="_blank"}. Lambda handler is actually called once (top-down)
* Async middlewares are not supported
