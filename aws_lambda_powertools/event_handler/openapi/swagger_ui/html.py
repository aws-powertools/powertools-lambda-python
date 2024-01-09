import json


def generate_swagger_html(spec: str, js_url: str, css_url: str) -> str:
    """
    Generate Swagger UI HTML page

    Parameters
    ----------
    spec: str
        The OpenAPI spec in the JSON format
    js_url: str
        The URL to the Swagger UI JavaScript file
    css_url: str
        The URL to the Swagger UI CSS file
    """

    # The .replace('</', '<\\/') part is necessary to prevent a potential issue where the JSON string contains
    # </script> or similar tags. Escaping the forward slash in </ as <\/ ensures that the JSON does not inadvertently
    # close the script tag, and the JSON remains a valid string within the JavaScript code.
    escaped_spec = json.dumps(json.loads(spec)).replace("</", "<\\/")

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
    <link rel="stylesheet" type="text/css" href="{css_url}">
</head>

<body>
    <div id="swagger-ui">
        Loading...
    </div>
</body>

<script src="{js_url}"></script>

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
