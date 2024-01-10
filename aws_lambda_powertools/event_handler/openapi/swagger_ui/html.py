def generate_swagger_html(spec: str, path: str, js_url: str, css_url: str) -> str:
    """
    Generate Swagger UI HTML page

    Parameters
    ----------
    spec: str
        The OpenAPI spec
    path: str
        The path to the Swagger documentation
    js_url: str
        The URL to the Swagger UI JavaScript file
    css_url: str
        The URL to the Swagger UI CSS file
    """

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
    spec: {spec},
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIBundle.SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ]
  }}

  var ui = SwaggerUIBundle(swaggerUIOptions)
  ui.specActions.updateUrl('{path}?format=json');
</script>
</html>
            """.strip()
