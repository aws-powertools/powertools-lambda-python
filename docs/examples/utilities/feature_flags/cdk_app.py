import json

import aws_cdk.aws_appconfig as appconfig
from aws_cdk import core


class SampleFeatureFlagStore(core.Construct):
    def __init__(self, scope: core.Construct, id_: str) -> None:
        super().__init__(scope, id_)

        features_config = {
            "premium_features": {
                "default": False,
                "rules": {
                    "customer tier equals premium": {
                        "when_match": True,
                        "conditions": [{"action": "EQUALS", "key": "tier", "value": "premium"}],
                    }
                },
            },
            "ten_percent_off_campaign": {"default": True},
        }

        self.config_app = appconfig.CfnApplication(
            self,
            id="app",
            name="product-catalogue",
        )
        self.config_env = appconfig.CfnEnvironment(
            self,
            id="env",
            application_id=self.config_app.ref,
            name="dev-env",
        )
        self.config_profile = appconfig.CfnConfigurationProfile(
            self,
            id="profile",
            application_id=self.config_app.ref,
            location_uri="hosted",
            name="features",
        )
        self.hosted_cfg_version = appconfig.CfnHostedConfigurationVersion(
            self,
            "version",
            application_id=self.config_app.ref,
            configuration_profile_id=self.config_profile.ref,
            content=json.dumps(features_config),
            content_type="application/json",
        )
        self.app_config_deployment = appconfig.CfnDeployment(
            self,
            id="deploy",
            application_id=self.config_app.ref,
            configuration_profile_id=self.config_profile.ref,
            configuration_version=self.hosted_cfg_version.ref,
            deployment_strategy_id="AppConfig.AllAtOnce",
            environment_id=self.config_env.ref,
        )
