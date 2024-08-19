from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities import parameters

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

ssm_provider = parameters.SSMProvider()


def lambda_handler(event: dict, context: LambdaContext):
    # This will display:
    # /param/a: [some value]
    # /param/b: [some value]
    # /param/c: None
    values: Any = ssm_provider.get_multiple("/param", transform="json")
    for key, value in values.items():
        print(f"{key}: {value}")

    try:
        # This will raise a TransformParameterError exception
        values = ssm_provider.get_multiple("/param", transform="json", raise_on_transform_error=True)
    except parameters.exceptions.TransformParameterError:
        ...
