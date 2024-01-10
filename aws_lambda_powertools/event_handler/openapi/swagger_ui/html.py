def generate_swagger_html(spec: str, path: str, swagger_js: str, swagger_css: str, swagger_base_url: str) -> str:
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
