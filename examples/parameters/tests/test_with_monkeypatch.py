from unittest.mock import patch

from src import single_mock


# Replaces "aws_lambda_powertools.utilities.parameters.get_parameter" with a Mock object
@patch("aws_lambda_powertools.utilities.parameters.get_parameter")
def test_handler(get_parameter_mock):
    get_parameter_mock.return_value = "mock_value"

    return_val = single_mock.handler({}, {})
    get_parameter_mock.assert_called_with("my-parameter-name")
    assert return_val.get("message") == "mock_value"
