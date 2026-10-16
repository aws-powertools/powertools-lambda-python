import os
import subprocess
import sys
from pathlib import Path

import pytest

MODEL_IMPORT_CASES = [
    ("SqsModel", "sqs", ["sqs"]),
    ("S3Model", "s3", ["s3", "event_bridge"]),
    ("AppSyncEventsModel", "appsync_events", ["appsync_events", "appsync"]),
    ("LambdaFunctionUrlModel", "lambda_function_url", ["lambda_function_url", "apigwv2"]),
    (
        "KinesisFirehoseSqsModel",
        "kinesis_firehose_sqs",
        ["kinesis_firehose_sqs", "kinesis_firehose", "sqs"],
    ),
    (
        "S3SqsEventNotificationModel",
        "s3_event_notification",
        ["s3_event_notification", "s3", "event_bridge", "sqs"],
    ),
]


def run_probe(*args: str):
    project_root = Path(__file__).parents[3]
    probe = Path(__file__).with_name("_model_import_probe.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    result = subprocess.run(
        [sys.executable, str(probe), *args],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("access", ["export", "submodule", "attribute"])
@pytest.mark.parametrize("name,module,dependencies", MODEL_IMPORT_CASES, ids=[case[0] for case in MODEL_IMPORT_CASES])
def test_model_import_loads_only_its_dependencies(access, name, module, dependencies):
    run_probe(access, name, module, *dependencies)


@pytest.mark.parametrize("scenario", ["lazy", "exports", "star", "introspection", "pickle", "concurrent"])
def test_model_import_compatibility(scenario):
    run_probe(scenario)
