from pydantic import BaseModel


class SqsSchema(BaseModel):
    todo: str
