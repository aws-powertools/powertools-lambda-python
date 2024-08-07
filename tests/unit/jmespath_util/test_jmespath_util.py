import pytest

from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning


def test_extract_data_from_envelope():
    data = {"data": {"foo": "bar"}}
    envelope = "data"

    with pytest.warns(PowertoolsDeprecationWarning, match="The extract_data_from_envelope method is deprecated in V3*"):
        assert extract_data_from_envelope(data=data, envelope=envelope) == {"foo": "bar"}
