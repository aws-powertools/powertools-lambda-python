"""Shared warnings that don't belong to a single utility"""


class PowertoolsUserWarning(UserWarning):
    """
    This class provides a custom Warning tailored for better clarity when certain situations occur.

     Examples:
    - Using development-only features in production environment.
    - Potential performance or security issues due to misconfiguration.

    Parameters
    ----------
    message: str
         The warning message to be displayed.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message


class PowertoolsDeprecationWarning(DeprecationWarning):
    """
    This class provides a DeprecationWarning custom Warning for utilities/parameters deprecated in v3.

     Examples:
    - Using development-only features in production environment.
    - Potential performance or security issues due to misconfiguration.

    Parameters
    ----------
    message: str
         The warning message to be displayed.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message
