---
title: Typing
description: Utility
---

<!-- markdownlint-disable MD043 -->

This typing utility provides static typing classes that can be used to ease the development by providing the IDE type hints.

## Key features

* Add static typing classes
* Ease the development by leveraging your IDE's type hints
* Avoid common typing mistakes in Python

![Utilities Typing](../media/utilities_typing_1.png)

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples){target="_blank"}.

We provide static typing for any context methods or properties implemented by [Lambda context object](https://docs.aws.amazon.com/lambda/latest/dg/python-context.html){target="_blank"}.

## LambdaContext

The `LambdaContext` typing is typically used in the handler method for the Lambda function.

=== "getting_started_validator_decorator_function.py"

	```python hl_lines="1 4"
    --8<-- "examples/typing/src/getting_started_typing_function.py"
	```

## Working with context methods and properties

Using `LambdaContext` typing makes it possible to access information and hints of all properties and methods implemented by Lambda context object.

=== "working_with_context_function.py"

	```python hl_lines="6 16 25 26"
    --8<-- "examples/typing/src/working_with_context_function.py"
	```

![Utilities Typing All](../media/utilities_typing_2.png)
![Utilities Typing Specific](../media/utilities_typing_3.png)
