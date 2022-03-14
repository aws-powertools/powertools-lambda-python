from aws_lambda_powertools.utilities.parser import BaseModel, parse, validator


class HelloWorldModel(BaseModel):
    message: str

    @validator("message")
    def is_hello_world(cls, v):
        if v != "hello world":
            raise ValueError("Message must be hello world!")
        return v


parse(model=HelloWorldModel, event={"message": "hello universe"})
