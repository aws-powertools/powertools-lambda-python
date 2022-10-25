from abc import ABC, abstractmethod
from pathlib import Path


class BaseLocalLambdaLayer(ABC):
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / "layer_build"
        self.target_dir = f"{self.output_dir}/python"

    @abstractmethod
    def build(self) -> str:
        """Builds a Lambda Layer locally

        Returns
        -------
        build_path : str
            Path where newly built Lambda Layer is
        """
        raise NotImplementedError()

    def before_build(self):
        """Any step to run before build process begins.

        By default, it creates output dir and its parents if it doesn't exist.
        """
        if not self.output_dir.exists():
            # Create missing parent directories if missing
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def after_build(self):  # noqa: B027
        """Any step after a build succeed"""
        ...
