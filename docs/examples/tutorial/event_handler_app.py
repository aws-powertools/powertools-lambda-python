from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/hello/<name>")
def hello_name(name):
    return {"message": f"hello {name}!"}


@app.get("/hello")
def hello():
    return {"message": "hello unknown!"}


def lambda_handler(event, context):
    return app.resolve(event, context)
