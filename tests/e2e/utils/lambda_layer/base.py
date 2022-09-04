from pathlib import Path

from abc import ABC, abstractmethod


class BaseLocalLambdaLayer(ABC):
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / "layer_build"
        self.target_dir = f"{self.output_dir}/python"

    @abstractmethod
    def build(self) -> str:
        raise NotImplementedError()

    def before_build(self):
        if not self.output_dir.exists():
            # Create missing parent directories if missing
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def after_build(self):
        ...
