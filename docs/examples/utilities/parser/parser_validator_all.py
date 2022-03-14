from aws_lambda_powertools.utilities.parser import BaseModel, parse, validator


class HelloWorldModel(BaseModel):
    message: str
    sender: str

    @validator("*")
    def has_whitespace(cls, v):
        if " " not in v:
            raise ValueError("Must have whitespace...")

        return v


parse(model=HelloWorldModel, event={"message": "hello universe", "sender": "universe"})
