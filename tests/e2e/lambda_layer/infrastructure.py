import logging
import subprocess

from tests.e2e.utils.infrastructure import CDK_OUT_PATH, SOURCE_CODE_ROOT_PATH

logger = logging.getLogger(__name__)


def build_layer(feature_name: str = "") -> str:
    LAYER_BUILD_PATH = CDK_OUT_PATH / f"layer_build_{feature_name}"

    # TODO: Check if source code hasn't changed (dirsum)
    package = f"{SOURCE_CODE_ROOT_PATH}\[pydantic\]"
    build_args = "--platform manylinux1_x86_64 --only-binary=:all: --upgrade"
    build_command = f"pip install {package} {build_args} --target {LAYER_BUILD_PATH}/python"
    subprocess.run(build_command, shell=True)

    return str(LAYER_BUILD_PATH)
