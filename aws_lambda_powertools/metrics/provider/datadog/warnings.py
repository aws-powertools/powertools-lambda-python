class DatadogDataValidationWarning(Warning):
    message: str

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message
