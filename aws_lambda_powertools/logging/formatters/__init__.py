"""Built-in Logger formatters for Observability Providers that require custom config."""

# NOTE: we don't expose formatters directly (barrel import)
# as we cannot know if they'll need additional dependencies in the future
# so we isolate to avoid a performance hit and workarounds like lazy imports
