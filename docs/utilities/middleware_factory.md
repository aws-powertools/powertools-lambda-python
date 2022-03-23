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

```python hl_lines="3-4 10" title="Creating your own middleware for before/after logic"
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

@lambda_handler_decorator
def middleware_before_after(handler, event, context):
	# logic_before_handler_execution()
	response = handler(event, context)
	# logic_after_handler_execution()
	return response

@middleware_before_after
def lambda_handler(event, context):
	...
```

## Middleware with params

You can also have your own keyword arguments after the mandatory arguments.

```python hl_lines="2 12" title="Accepting arbitrary keyword arguments"
@lambda_handler_decorator
def obfuscate_sensitive_data(handler, event, context, fields: List = None):
	# Obfuscate email before calling Lambda handler
	if fields:
		for field in fields:
			if field in event:
				event[field] = obfuscate(event[field])

	return handler(event, context)

@obfuscate_sensitive_data(fields=["email"])
def lambda_handler(event, context):
	...
```

## Tracing middleware execution

If you are making use of [Tracer](../core/tracer.md), you can trace the execution of your middleware to ease operations.

This makes use of an existing Tracer instance that you may have initialized anywhere in your code.

```python hl_lines="3" title="Tracing custom middlewares with Tracer"
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

@lambda_handler_decorator(trace_execution=True)
def my_middleware(handler, event, context):
	return handler(event, context)

@my_middleware
def lambda_handler(event, context):
	...
```

When executed, your middleware name will [appear in AWS X-Ray Trace details as](../core/tracer.md) `## middleware_name`.

For advanced use cases, you can instantiate [Tracer](../core/tracer.md) inside your middleware, and add annotations as well as metadata for additional operational insights.

```python hl_lines="6-8" title="Add custom tracing insights before/after in your middlware"
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools import Tracer

@lambda_handler_decorator(trace_execution=True)
def middleware_name(handler, event, context):
	# tracer = Tracer() # Takes a copy of an existing tracer instance
	# tracer.add_annotation...
	# tracer.add_metadata...
	return handler(event, context)
```

## Tips

* Use `trace_execution` to quickly understand the performance impact of your middlewares, and reduce or merge tasks when necessary
* When nesting multiple middlewares, always return the handler with event and context, or response
* Keep in mind [Python decorators execution order](https://realpython.com/primer-on-python-decorators/#nesting-decorators){target="_blank"}. Lambda handler is actually called once (top-down)
* Async middlewares are not supported
