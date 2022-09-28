import os
import re
from pathlib import Path

from mkdocs.config import Config
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


def inject(markdown: str, page: Page, config: Config, files: Files):
    if not page.is_homepage:
        return markdown

    # Try to see if we have a cdk-layer-stack directory.
    # This is created during the layer build, saved as an artifact, and downloaded before the jobs runs
    if not os.path.exists("cdk-layer-stack"):
        print("No cdk-layer-stack directory found, not replacing lambda layer versions")
        return markdown

    # For each cdk output file, replace all the lambda layer occurrences in the docs
    files = Path("cdk-layer-stack").glob("*")
    for cdk_file in files:
        with open(cdk_file, "r") as f:
            layer_version_arn = f.readlines()[0].strip()
            layer_version_prefix = ":".join(layer_version_arn.split(":")[:-1])

            # replace the prefix with the new version
            markdown = re.sub(rf"{layer_version_prefix}:\d+", layer_version_arn, markdown)

    return markdown
