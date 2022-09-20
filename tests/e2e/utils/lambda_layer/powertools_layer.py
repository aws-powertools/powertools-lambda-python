import logging
import subprocess
from pathlib import Path

from checksumdir import dirhash

from aws_lambda_powertools import PACKAGE_PATH
from tests.e2e.utils.constants import CDK_OUT_PATH, SOURCE_CODE_ROOT_PATH
from tests.e2e.utils.lambda_layer.base import BaseLocalLambdaLayer

logger = logging.getLogger(__name__)


class LocalLambdaPowertoolsLayer(BaseLocalLambdaLayer):
    IGNORE_EXTENSIONS = ["pyc"]

    def __init__(self, output_dir: Path = CDK_OUT_PATH):
        super().__init__(output_dir)
        self.package = f"{SOURCE_CODE_ROOT_PATH}[pydantic]"
        self.build_args = "--platform manylinux1_x86_64 --only-binary=:all: --upgrade"
        self.build_command = f"python -m pip install {self.package} {self.build_args} --target {self.target_dir}"
        self.source_diff_file: Path = CDK_OUT_PATH / "layer_build.diff"

    def build(self) -> str:
        self.before_build()

        if self._has_source_changed():
            subprocess.run(self.build_command, shell=True)

        self.after_build()

        return str(self.output_dir)

    def _has_source_changed(self) -> bool:
        """Hashes source code and

        Returns
        -------
        change : bool
            Whether source code hash has changed
        """
        diff = self.source_diff_file.read_text() if self.source_diff_file.exists() else ""
        new_diff = dirhash(dirname=PACKAGE_PATH, excluded_extensions=self.IGNORE_EXTENSIONS)
        if new_diff != diff or not self.output_dir.exists():
            self.source_diff_file.write_text(new_diff)
            return True

        return False
