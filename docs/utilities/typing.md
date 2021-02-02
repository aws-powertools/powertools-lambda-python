---
title: Typing
description: Utility
---

This typing utility provides static typing classes that can be used to ease the development by providing the IDE type hints.

![Utilities Typing](../media/utilities_typing.png)

## LambdaContext

The `LambdaContext` typing is typically used in the handler method for the Lambda function.

=== "index.py"

    ```python hl_lines="4"
    from typing import Any, Dict
    from aws_lambda_powertools.utilities.typing import LambdaContext

    def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
        # Insert business logic
        return event
    ```
