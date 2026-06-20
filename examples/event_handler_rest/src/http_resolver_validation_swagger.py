from pydantic import BaseModel

from aws_lambda_powertools.event_handler import HttpResolver


class User(BaseModel):
    name: str
    age: int


app = HttpResolver(enable_validation=True)

app.enable_swagger(
    title="My API",
    version="1.0.0",
)


@app.post("/users")
def create_user(user: User) -> dict:
    return {"id": "123", "user": user.model_dump()}


handler = app
