from pathlib import Path

from aws_cdk import AssetStaging, BundlingOptions, CfnOutput, DockerImage
from aws_cdk.aws_lambda import Code, LayerVersion

from tests.e2e.utils.infrastructure import (
    PYTHON_RUNTIME_VERSION,
    SOURCE_CODE_ROOT_PATH,
    BaseInfrastructure,
    PythonVersion,
    logger,
)


class LambdaLayerStack(BaseInfrastructure):
    FEATURE_NAME = "lambda-layer"

    def __init__(self, handlers_dir: Path, feature_name: str = FEATURE_NAME, layer_arn: str = "") -> None:
        super().__init__(feature_name, handlers_dir, layer_arn)

    def create_resources(self):
        layer = self._create_layer()
        CfnOutput(self.stack, "LayerArn", value=layer)

    def _create_layer(self) -> str:
        logger.debug("Creating Lambda Layer with latest source code available")
        output_dir = Path(str(AssetStaging.BUNDLING_OUTPUT_DIR), "python")
        input_dir = Path(str(AssetStaging.BUNDLING_INPUT_DIR), "aws_lambda_powertools")

        build_commands = [f"pip install .[pydantic] -t {output_dir}", f"cp -R {input_dir} {output_dir}"]
        layer = LayerVersion(
            self.stack,
            "aws-lambda-powertools-e2e-test",
            layer_version_name="aws-lambda-powertools-e2e-test",
            compatible_runtimes=[PythonVersion[PYTHON_RUNTIME_VERSION].value["runtime"]],
            code=Code.from_asset(
                path=str(SOURCE_CODE_ROOT_PATH),
                bundling=BundlingOptions(
                    image=DockerImage.from_build(
                        str(Path(__file__).parent),
                        build_args={"IMAGE": PythonVersion[PYTHON_RUNTIME_VERSION].value["image"]},
                    ),
                    command=["bash", "-c", " && ".join(build_commands)],
                ),
            ),
        )
        return layer.layer_version_arn
