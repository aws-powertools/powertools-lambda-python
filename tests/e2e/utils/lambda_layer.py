import subprocess
from pathlib import Path

from tests.e2e.utils.constants import LAYER_BUILD_PATH, SOURCE_CODE_ROOT_PATH


# TODO: Move to BaseInfra to ensure outdir includes feature_name
def build_layer() -> str:
    # TODO: Check if source code hasn't changed (dirsum)
    package = f"{SOURCE_CODE_ROOT_PATH}\[pydantic\]"
    build_args = "--platform manylinux1_x86_64 --only-binary=:all: --upgrade"
    build_command = f"pip install {package} {build_args} --target {LAYER_BUILD_PATH}/python"
    subprocess.run(build_command, shell=True)

    return str(LAYER_BUILD_PATH)


# NOTE: For later
class LambdaLayer:
    def __init__(self, output_dir: Path, package_name: str, build_command: str):
        self.output_dir = output_dir
        self.package_name = package_name
        self.build_command = build_command

    def build(self):
        if not self.output_dir.exists():
            self.output_dir.mkdir()

        subprocess.run(self.build_command, shell=True)

    def before(self):
        ...

    def after(self):
        ...
