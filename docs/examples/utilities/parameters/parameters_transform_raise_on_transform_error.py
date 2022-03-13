from aws_lambda_powertools.utilities import parameters

ssm_provider = parameters.SSMProvider()


def handler(event, context):
    # This will display:
    # /param/a: [some value]
    # /param/b: [some value]
    # /param/c: None
    values = ssm_provider.get_multiple("/param", transform="json")
    for k, v in values.items():
        print(f"{k}: {v}")

    try:
        # This will raise a TransformParameterError exception
        values = ssm_provider.get_multiple("/param", transform="json", raise_on_transform_error=True)
    except parameters.exceptions.TransformParameterError:
        ...
