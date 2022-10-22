""" Calculate how many parallel workers are needed to complete E2E infrastructure jobs across available CPU Cores """
import subprocess
from pathlib import Path


def main():
    features = Path("tests/e2e").rglob("infrastructure.py")
    workers = len(list(features)) - 1

    command = f"poetry run pytest -n {workers} --dist loadfile -o log_cli=true tests/e2e"
    subprocess.run(command.split(), shell=False)


if __name__ == "__main__":
    main()
