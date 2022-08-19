from aws_lambda_powertools.event_handler import ALBResolver, Response, content_types

app = ALBResolver()


@app.route("/todos", method=["GET"])
def hello():
    return Response(
        status_code=200,
        content_type=content_types.TEXT_PLAIN,
        body="Hello world",
        cookies=["CookieMonster; Secure", "MonsterCookie"],
        headers={"Foo": ["bar", "zbr"]},
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
