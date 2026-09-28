import importlib
import inspect
import sys

ENVELOPE_MODULE = "aws_lambda_powertools.utilities.parser.envelopes"
scenario = sys.argv[1]

if scenario == "lazy":
    parser = importlib.import_module("aws_lambda_powertools.utilities.parser")

    assert not any(module == ENVELOPE_MODULE or module.startswith(f"{ENVELOPE_MODULE}.") for module in sys.modules)
    assert {"envelopes", "BaseEnvelope"} <= set(dir(parser))
    assert ENVELOPE_MODULE not in sys.modules

    members = dict(inspect.getmembers(parser))
    assert members["envelopes"] is parser.envelopes
    assert members["BaseEnvelope"] is parser.BaseEnvelope
    assert ENVELOPE_MODULE in sys.modules
elif scenario == "star":
    from aws_lambda_powertools.utilities.parser import *  # noqa: E402,F403

    expected = {
        "parse",
        "event_parser",
        "envelopes",
        "BaseEnvelope",
    }
    assert expected <= globals().keys()
    assert ENVELOPE_MODULE in sys.modules
else:
    raise ValueError(f"Unknown scenario: {scenario}")
