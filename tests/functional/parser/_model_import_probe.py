import importlib
import inspect
import json
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import get_args, get_type_hints

PACKAGE = "aws_lambda_powertools.utilities.parser.models"
scenario = sys.argv[1]
models = importlib.import_module(PACKAGE)


def loaded_models():
    return {name.removeprefix(f"{PACKAGE}.") for name in sys.modules if name.startswith(f"{PACKAGE}.")}


if scenario == "lazy":
    assert not loaded_models(), loaded_models()
    assert set(models.__all__) | {"sqs", "alb"} <= set(dir(models))
    assert not loaded_models(), "dir() must not load models"
    try:
        _ = models.nonexistent_model
    except AttributeError as exc:
        assert str(exc) == f"module {PACKAGE!r} has no attribute 'nonexistent_model'"
    else:
        raise AssertionError("Unknown exports must raise AttributeError")
    assert not loaded_models()
elif scenario in {"export", "submodule", "attribute"}:
    name, module, *dependencies = sys.argv[2:]
    if scenario == "export":
        # Exercise Python's from-import handling as well as attribute lookup.
        package = __import__(PACKAGE, fromlist=[name])
        model = getattr(package, name)
    elif scenario == "submodule":
        model = getattr(importlib.import_module(f"{PACKAGE}.{module}"), name)
    else:
        model = getattr(getattr(models, module), name)
    assert loaded_models() == set(dependencies), loaded_models()
    assert getattr(models, name) is model
    assert vars(models)[name] is model, "The resolved export must be cached"
    assert getattr(getattr(models, module), name) is model
    assert loaded_models() == set(dependencies), loaded_models()
elif scenario == "exports":
    for name in models.__all__:
        model = getattr(models, name)
        original = getattr(importlib.import_module(model.__module__), model.__name__)
        assert model is original, name
        assert pickle.loads(pickle.dumps(model)) is model, name
    assert get_args(get_type_hints(models.SqsModel)["Records"]) == (models.SqsRecordModel,)
elif scenario == "star":
    from aws_lambda_powertools.utilities.parser.models import *  # noqa: E402,F403

    for name in models.__all__:
        assert globals()[name] is getattr(models, name), name
elif scenario == "introspection":
    members = dict(inspect.getmembers(models))
    assert set(models.__all__) <= members.keys()
    assert members["sqs"] is importlib.import_module(f"{PACKAGE}.sqs")
    assert members["SqsModel"] is members["sqs"].SqsModel
elif scenario == "pickle":
    from aws_lambda_powertools.utilities.parser.models import SqsModel

    event = json.loads((Path(__file__).parents[2] / "events" / "sqsEvent.json").read_text())
    parsed = SqsModel.model_validate(event)
    restored = pickle.loads(pickle.dumps(parsed))
    assert type(restored) is SqsModel
    assert restored.model_dump() == parsed.model_dump()
    assert loaded_models() == {"sqs"}
elif scenario == "concurrent":
    names = ["SqsModel", "S3Model", "S3SqsEventNotificationModel", "KinesisFirehoseSqsModel"] * 4
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda name: getattr(models, name), names))
    for name, model in zip(names, results, strict=True):
        assert model is getattr(models, name), name
    assert loaded_models() == {
        "sqs",
        "s3",
        "event_bridge",
        "s3_event_notification",
        "kinesis_firehose_sqs",
        "kinesis_firehose",
    }
else:
    raise ValueError(f"Unknown scenario: {scenario}")
