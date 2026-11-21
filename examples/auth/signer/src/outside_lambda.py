import botocore.session

from aws_lambda_powertools.utilities.auth import SigV4Signer

# Outside Lambda the environment variables may be missing; let botocore's provider chain
# find credentials (profile, SSO, instance role) and name the region explicitly.
signer = SigV4Signer(
    service="execute-api",
    region="eu-west-1",
    session=botocore.session.get_session(),
)

signed = signer.sign("GET", "https://abc123.execute-api.eu-west-1.amazonaws.com/prod/orders")
print(signed.headers["Authorization"])
