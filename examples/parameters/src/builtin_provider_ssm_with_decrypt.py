from typing import Any
from uuid import uuid4

import boto3

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

ec2 = boto3.resource("ec2")
ssm_provider = parameters.SSMProvider()


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve the key pair from secure string parameter
        ec2_pem: Any = ssm_provider.get("/lambda-powertools/ec2_pem", decrypt=True)

        name_key_pair = f"kp_{uuid4()}"

        ec2.import_key_pair(KeyName=name_key_pair, PublicKeyMaterial=ec2_pem)

        ec2.create_instances(
            ImageId="ami-026b57f3c383c2eec",
            InstanceType="t2.micro",
            MinCount=1,
            MaxCount=1,
            KeyName=name_key_pair,
        )

        return {"message": "EC2 created", "success": True}
    except parameters.exceptions.GetParameterError as error:
        return {"message": f"Error creating EC2 => {str(error)}", "success": False}
