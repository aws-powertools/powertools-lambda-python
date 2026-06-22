from aws_lambda_powertools.event_handler import HttpResolver

app = HttpResolver()


@app.get("/hello/<name>")
def hello(name: str):
    return {"message": f"Hello, {name}!"}


# Lambda handler - same code works in Lambda
handler = app
