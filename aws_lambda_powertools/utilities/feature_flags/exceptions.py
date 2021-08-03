class ConfigurationStoreError(Exception):
    """When a configuration store raises an exception on config retrieval or parsing"""


class SchemaValidationError(Exception):
    """When feature flag schema fails validation"""
