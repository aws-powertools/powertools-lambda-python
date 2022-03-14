from aws_lambda_powertools.utilities.parser import BaseModel, parse, root_validator


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str

    @root_validator
    def check_passwords_match(cls, values):
        pw1, pw2 = values.get("password1"), values.get("password2")
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("passwords do not match")
        return values


payload = {
    "username": "universe",
    "password1": "myp@ssword",
    "password2": "repeat password",
}

parse(model=UserModel, event=payload)
