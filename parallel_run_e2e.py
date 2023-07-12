""" Calculate how many parallel workers are needed to complete E2E infrastructure jobs across available CPU Cores """
import subprocess
import sys
from pathlib import Path


def main():
    features = Path("tests/e2e").rglob("infrastructure.py")
    workers = len(list(features)) - 1

    command = f"poetry run pytest -n {workers} -o log_cli=true tests/e2e"
    result = subprocess.run(command.split(), shell=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
