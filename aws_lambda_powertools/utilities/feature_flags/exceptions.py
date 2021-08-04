class ConfigurationStoreError(Exception):
    """When a configuration store raises an exception on config retrieval or parsing"""


class SchemaValidationError(Exception):
    """When feature flag schema fails validation"""


class StoreClientError(Exception):
    """When a store raises an exception that should be propagated to the client to fix

    For example, Access Denied errors when the client doesn't permissions to fetch config
    """
