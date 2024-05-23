class PowertoolsWarning(UserWarning):
    """
    This class provides a custom Warning tailored for better clarity when certain situations occur.
    It offers more informative and relevant warning messages, allowing customers to easily suppress
    or handle this specific warning type as needed.

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
