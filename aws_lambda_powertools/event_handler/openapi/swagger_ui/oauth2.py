# ruff: noqa: E501 FA100
import warnings
from typing import Dict, Optional, Sequence

from pydantic import BaseModel, Field, field_validator

from aws_lambda_powertools.event_handler.openapi.models import (
    MODEL_CONFIG_ALLOW,
)
from aws_lambda_powertools.shared.functions import powertools_dev_is_set


# Based on https://swagger.io/docs/open-source-tools/swagger-ui/usage/oauth2/
class OAuth2Config(BaseModel):
    """
    OAuth2 configuration for Swagger UI
    """

    # The client ID for the OAuth2 application
    clientId: Optional[str] = Field(alias="client_id", default=None)

    # The client secret for the OAuth2 application. This is sensitive information and requires the explicit presence
    # of the POWERTOOLS_DEV environment variable.
    clientSecret: Optional[str] = Field(alias="client_secret", default=None)

    # The realm in which the OAuth2 application is registered. Optional.
    realm: Optional[str] = Field(default=None)

    # The name of the OAuth2 application
    appName: str = Field(alias="app_name")

    # The scopes that the OAuth2 application requires. Defaults to an empty list.
    scopes: Sequence[str] = Field(default=[])

    # Additional query string parameters to be included in the OAuth2 request. Defaults to an empty dictionary.
    additionalQueryStringParams: Dict[str, str] = Field(alias="additional_query_string_params", default={})

    # Whether to use basic authentication with the access code grant type. Defaults to False.
    useBasicAuthenticationWithAccessCodeGrant: bool = Field(
        alias="use_basic_authentication_with_access_code_grant",
        default=False,
    )

    # Whether to use PKCE with the authorization code grant type. Defaults to False.
    usePkceWithAuthorizationCodeGrant: bool = Field(alias="use_pkce_with_authorization_code_grant", default=False)

    model_config = MODEL_CONFIG_ALLOW

    @field_validator("clientSecret")
    def client_secret_only_on_dev(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None

        if not powertools_dev_is_set():
            raise ValueError(
                "cannot use client_secret without POWERTOOLS_DEV mode. See "
                "https://docs.powertools.aws.dev/lambda/python/latest/#optimizing-for-non-production-environments",
            )
        else:
            warnings.warn(
                "OAuth2Config is using client_secret and POWERTOOLS_DEV is set. This reveals sensitive information. "
                "DO NOT USE THIS OUTSIDE LOCAL DEVELOPMENT",
                stacklevel=2,
            )
            return v


def generate_oauth2_redirect_html() -> str:
    """
    Generates the HTML content for the OAuth2 redirect page.

    Source: https://github.com/swagger-api/swagger-ui/blob/master/dist/oauth2-redirect.html
    """
    return """
<!doctype html>
<html lang="en-US">
<head>
    <title>Swagger UI: OAuth2 Redirect</title>
</head>
<body>
<script>
    'use strict';
    function run () {
        var oauth2 = window.opener.swaggerUIRedirectOauth2;
        var sentState = oauth2.state;
        var redirectUrl = oauth2.redirectUrl;
        var isValid, qp, arr;

        if (/code|token|error/.test(window.location.hash)) {
            qp = window.location.hash.substring(1).replace('?', '&');
        } else {
            qp = location.search.substring(1);
        }

        arr = qp.split("&");
        arr.forEach(function (v,i,_arr) { _arr[i] = '"' + v.replace('=', '":"') + '"';});
        qp = qp ? JSON.parse('{' + arr.join() + '}',
                function (key, value) {
                    return key === "" ? value : decodeURIComponent(value);
                }
        ) : {};

        isValid = qp.state === sentState;

        if ((
          oauth2.auth.schema.get("flow") === "accessCode" ||
          oauth2.auth.schema.get("flow") === "authorizationCode" ||
          oauth2.auth.schema.get("flow") === "authorization_code"
        ) && !oauth2.auth.code) {
            if (!isValid) {
                oauth2.errCb({
                    authId: oauth2.auth.name,
                    source: "auth",
                    level: "warning",
                    message: "Authorization may be unsafe, passed state was changed in server. The passed state wasn't returned from auth server."
                });
            }

            if (qp.code) {
                delete oauth2.state;
                oauth2.auth.code = qp.code;
                oauth2.callback({auth: oauth2.auth, redirectUrl: redirectUrl});
            } else {
                let oauthErrorMsg;
                if (qp.error) {
                    oauthErrorMsg = "["+qp.error+"]: " +
                        (qp.error_description ? qp.error_description+ ". " : "no accessCode received from the server. ") +
                        (qp.error_uri ? "More info: "+qp.error_uri : "");
                }

                oauth2.errCb({
                    authId: oauth2.auth.name,
                    source: "auth",
                    level: "error",
                    message: oauthErrorMsg || "[Authorization failed]: no accessCode received from the server."
                });
            }
        } else {
            oauth2.callback({auth: oauth2.auth, token: qp, isValid: isValid, redirectUrl: redirectUrl});
        }
        window.close();
    }

    if (document.readyState !== 'loading') {
        run();
    } else {
        document.addEventListener('DOMContentLoaded', function () {
            run();
        });
    }
</script>
</body>
</html>
    """.strip()
