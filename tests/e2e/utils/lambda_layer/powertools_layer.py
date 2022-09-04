import logging
import subprocess
from pathlib import Path

from tests.e2e.utils.constants import SOURCE_CODE_ROOT_PATH
from tests.e2e.utils.lambda_layer.base import BaseLocalLambdaLayer

logger = logging.getLogger(__name__)


class LocalLambdaPowertoolsLayer(BaseLocalLambdaLayer):
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.package = f"{SOURCE_CODE_ROOT_PATH}\[pydantic\]"
        self.build_args = "--platform manylinux1_x86_64 --only-binary=:all: --upgrade"
        self.build_command = f"python -m pip install {self.package} {self.build_args} --target {self.target_dir}"

    def build(self) -> str:
        self.before_build()

        subprocess.run(self.build_command, shell=True)

        self.after_build()

        return str(self.output_dir)
