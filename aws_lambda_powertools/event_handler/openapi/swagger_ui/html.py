from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.openapi.swagger_ui.oauth2 import OAuth2Config


def generate_swagger_html(
    spec: str,
    swagger_js: str,
    swagger_css: str,
    swagger_base_url: str,
    oauth2_config: OAuth2Config | None,
    persist_authorization: bool = False,
) -> str:
    """
    Generate Swagger UI HTML page

    Parameters
    ----------
    spec: str
        The OpenAPI spec
    swagger_js: str
        Swagger UI JavaScript source code or URL
    swagger_css: str
        Swagger UI CSS source code or URL
    swagger_base_url: str
        The base URL for Swagger UI
    oauth2_config: OAuth2Config, optional
        The OAuth2 configuration.
    persist_authorization: bool, optional
        Whether to persist authorization data on browser close/refresh.
    """

    # If Swagger base URL is present, generate HTML content with linked CSS and JavaScript files
    # If no Swagger base URL is provided, include CSS and JavaScript directly in the HTML
    if swagger_base_url:
        swagger_css_content = f"<link rel='stylesheet' type='text/css' href='{swagger_css}'>"
        swagger_js_content = f"<script src='{swagger_js}'></script>"
    else:
        swagger_css_content = f"<style>{swagger_css}</style>"
        swagger_js_content = f"<script>{swagger_js}</script>"

    # Prepare oauth2 config
    oauth2_content = (
        f"ui.initOAuth({oauth2_config.json(exclude_none=True, exclude_unset=True)});" if oauth2_config else ""
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Swagger UI</title>
    <meta
      http-equiv="Cache-control"
      content="no-cache, no-store, must-revalidate"
    />
    {swagger_css_content}
</head>

<body>
    <div id="swagger-ui">
        Loading...
    </div>
</body>

{swagger_js_content}

<script>
  var currentUrl = new URL(window.location.href);
  var baseUrl = currentUrl.protocol + "//" + currentUrl.host + currentUrl.pathname;

  var swaggerUIOptions = {{
    dom_id: "#swagger-ui",
    docExpansion: "list",
    deepLinking: true,
    filter: true,
    layout: "BaseLayout",
    showExtensions: true,
    showCommonExtensions: true,
    spec: {spec},
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIBundle.SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    withCredentials: true,
    persistAuthorization: {str(persist_authorization).lower()},
    oauth2RedirectUrl: baseUrl + "?format=oauth2-redirect",
  }}

  var ui = SwaggerUIBundle(swaggerUIOptions)
  ui.specActions.updateUrl(currentUrl.pathname + "?format=json");
  {oauth2_content}
</script>
</html>
            """.strip()
