from aws_lambda_powertools.utilities import parameters

ssm_provider = parameters.SSMProvider()


def handler(event, context):
    decrypted_value = ssm_provider.get("/my/encrypted/parameter", decrypt=True)

    no_recursive_values = ssm_provider.get_multiple("/my/path/prefix", recursive=False)
