from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge

merge = OpenAPIMerge(title="API", version="1.0.0")

# Use project_root to resolve absolute imports like "from myapp.shared_resolver import app"
merge.discover(
    path="./src/myapp",
    pattern="shared_resolver.py",
    project_root="./src",  # Root for import resolution
)

# Automatically finds users_routes.py and orders_routes.py
# that import from shared_resolver.py
