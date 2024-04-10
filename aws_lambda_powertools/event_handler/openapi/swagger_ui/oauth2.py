from typing import Dict, Sequence

from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler.openapi.pydantic_loader import PYDANTIC_V2


# Based on https://swagger.io/docs/open-source-tools/swagger-ui/usage/oauth2/
class OAuth2Config(BaseModel):
    clientId: str = Field(alias="client_id")
    realm: str
    appName: str = Field(alias="app_name")
    scopes: Sequence[str] = Field(default=[])
    additionalQueryStringParams: Dict[str, str] = Field(alias="additional_query_string_params", default={})
    useBasicAuthenticationWithAccessCodeGrant: bool = Field(
        alias="use_basic_authentication_with_access_code_grant",
        default=False,
    )
    usePkceWithAuthorizationCodeGrant: bool = Field(alias="use_pkce_with_authorization_code_grant", default=False)

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}
    else:

        class Config:
            extra = "allow"
            allow_population_by_field_name = True
