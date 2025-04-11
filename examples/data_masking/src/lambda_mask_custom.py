class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def dict(self):
        return {"name": self.name, "age": self.age}


def lambda_handler(event, context):
    from aws_lambda_powertools.utilities.data_masking import DataMasking

    user = User("powertools", 42)
    masked = DataMasking().erase(user, fields=["age"])
    return masked
