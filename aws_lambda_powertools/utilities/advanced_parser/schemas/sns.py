from pydantic import BaseModel


class SnsSchema(BaseModel):
    todo: str
