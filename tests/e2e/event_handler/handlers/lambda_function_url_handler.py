from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver, Response, content_types

app = LambdaFunctionUrlResolver()


@app.get("/todos")
def hello():
    return Response(
        status_code=200,
        content_type=content_types.TEXT_PLAIN,
        body="Hello world",
        cookies=["CookieMonster", "MonsterCookie"],
        headers={"Foo": ["bar", "zbr"]},
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
