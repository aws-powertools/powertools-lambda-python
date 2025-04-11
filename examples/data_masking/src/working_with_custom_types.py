from aws_lambda_powertools.utilities.data_masking import DataMasking

data_masker = DataMasking()


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def dict(self):
        return {"name": self.name, "age": self.age}


def lambda_handler(event, context):
    user = User("powertools", 42)
    return data_masker.erase(user, fields=["age"])
