import json


def hello_name(event, **kargs):
    username = event["pathParameters"]["name"]
    return {"statusCode": 200, "body": json.dumps({"message": f"hello {username}!"})}


def hello(**kargs):
    return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


class Router:
    def __init__(self):
        self.routes = {}

    def set(self, path, method, handler):
        self.routes[f"{path}-{method}"] = handler

    def get(self, path, method):
        try:
            route = self.routes[f"{path}-{method}"]
        except KeyError:
            raise RuntimeError(f"Cannot route request to the correct method. path={path}, method={method}")
        return route


router = Router()
router.set(path="/hello", method="GET", handler=hello)
router.set(path="/hello/{name}", method="GET", handler=hello_name)


def lambda_handler(event, context):
    path = event["resource"]
    http_method = event["httpMethod"]
    method = router.get(path=path, method=http_method)
    return method(event=event)
