"""
Docs Workaround Router - Gate 0 Emergency Fix
Manually serves Swagger UI since FastAPI's built-in docs aren't mounting
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """
    Manually serve Swagger UI HTML pointing to /openapi.json
    """
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Scholarship Discovery & Search API - Swagger UI</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
        <style>
          body {
            margin: 0;
            padding: 0;
          }
        </style>
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
        <script>
          window.onload = function() {
            window.ui = SwaggerUIBundle({
              url: '/openapi.json',
              dom_id: '#swagger-ui',
              deepLinking: true,
              presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
              ],
              plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
              ],
              layout: "StandaloneLayout"
            })
          }
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/redoc", include_in_schema=False)
async def custom_redoc():
    """
    Manually serve ReDoc HTML pointing to /openapi.json
    """
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Scholarship Discovery & Search API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
          body {
            margin: 0;
            padding: 0;
          }
        </style>
      </head>
      <body>
        <redoc spec-url='/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)
