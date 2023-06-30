from aws_lambda_powertools.utilities.feature_flags import (
    AppConfigStore,
    FeatureFlags,
    RuleAction,
)


def init_feature_flags(mocker, mock_schema, envelope="") -> FeatureFlags:
    """Mock AppConfig Store get_configuration method to use mock schema instead"""

    method_to_mock = "aws_lambda_powertools.utilities.feature_flags.AppConfigStore.get_configuration"
    mocked_get_conf = mocker.patch(method_to_mock)
    mocked_get_conf.return_value = mock_schema

    app_conf_store = AppConfigStore(
        environment="test_env",
        application="test_app",
        name="test_conf_name",
        envelope=envelope,
    )

    return FeatureFlags(store=app_conf_store)


def test_flags_condition_match(mocker):
    # GIVEN
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id equals 12345": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant_id",
                            "value": "12345",
                        },
                    ],
                },
            },
        },
    }

    # WHEN
    ctx = {"tenant_id": "12345", "username": "a"}
    feature_flags = init_feature_flags(mocker=mocker, mock_schema=mocked_app_config_schema)
    flag = feature_flags.evaluate(name="my_feature", context=ctx, default=False)

    # THEN
    assert flag == expected_value
