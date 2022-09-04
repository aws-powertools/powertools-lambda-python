import subprocess
from pathlib import Path

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
