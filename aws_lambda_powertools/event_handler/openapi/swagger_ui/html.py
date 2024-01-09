from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.openapi.models import OpenAPI


def generate_swagger_html(spec: "OpenAPI", swagger_js: str, swagger_css: str, swagger_base_url: str) -> str:
    """
    Generate Swagger UI HTML page

    Parameters
    ----------
    spec: OpenAPI
        The OpenAPI spec
    js_url: str
        The URL to the Swagger UI JavaScript file
    css_url: str
        The URL to the Swagger UI CSS file
    """

    from aws_lambda_powertools.event_handler.openapi.compat import model_json

    # The .replace('</', '<\\/') part is necessary to prevent a potential issue where the JSON string contains
    # </script> or similar tags. Escaping the forward slash in </ as <\/ ensures that the JSON does not inadvertently
    # close the script tag, and the JSON remains a valid string within the JavaScript code.
    escaped_spec = model_json(
        spec,
        by_alias=True,
        exclude_none=True,
        indent=2,
    ).replace("</", "<\\/")

    # If Swagger base URL is present, generate HTML content with linked CSS and JavaScript files
    # If no Swagger base URL is provided, include CSS and JavaScript directly in the HTML
    if swagger_base_url:
        swagger_css_content = f"<link rel='stylesheet' type='text/css' href='{swagger_css}'>"
        swagger_js_content = f"<script src='{swagger_js}'></script>"
    else:
        swagger_css_content = f"<style>{swagger_css}</style>"
        swagger_js_content = f"<script>{swagger_js}</script>"

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
  var swaggerUIOptions = {{
    dom_id: "#swagger-ui",
    docExpansion: "list",
    deepLinking: true,
    filter: true,
    layout: "BaseLayout",
    showExtensions: true,
    showCommonExtensions: true,
    spec: {escaped_spec},
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIBundle.SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ]
  }}

  var ui = SwaggerUIBundle(swaggerUIOptions)
</script>
</html>
            """.strip()
