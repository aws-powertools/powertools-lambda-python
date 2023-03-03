from typing import List


from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

app = AppSyncResolver()


posts = {
    "1": {
        "id": "1",
        "title": "First book",
        "author": "Author1",
        "url": "https://amazon.com/",
        "content": "SAMPLE TEXT AUTHOR 1 SAMPLE TEXT AUTHOR 1 SAMPLE TEXT AUTHOR 1 SAMPLE TEXT AUTHOR 1 SAMPLE TEXT AUTHOR 1 SAMPLE TEXT AUTHOR 1",
        "ups": "100",
        "downs": "10",
    },
    "2": {
        "id": "2",
        "title": "Second book",
        "author": "Author2",
        "url": "https://amazon.com",
        "content": "SAMPLE TEXT AUTHOR 2 SAMPLE TEXT AUTHOR 2 SAMPLE TEXT",
        "ups": "100",
        "downs": "10",
    },
    "3": {
        "id": "3",
        "title": "Third book",
        "author": "Author3",
        "url": None,
        "content": None,
        "ups": None,
        "downs": None,
    },
    "4": {
        "id": "4",
        "title": "Fourth book",
        "author": "Author4",
        "url": "https://www.amazon.com/",
        "content": "SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4 SAMPLE TEXT AUTHOR 4",
        "ups": "1000",
        "downs": "0",
    },
    "5": {
        "id": "5",
        "title": "Fifth book",
        "author": "Author5",
        "url": "https://www.amazon.com/",
        "content": "SAMPLE TEXT AUTHOR 5 SAMPLE TEXT AUTHOR 5 SAMPLE TEXT AUTHOR 5 SAMPLE TEXT AUTHOR 5 SAMPLE TEXT",
        "ups": "50",
        "downs": "0",
    },
}

posts_related = {
    "1": [posts["4"]],
    "2": [posts["3"], posts["5"]],
    "3": [posts["2"], posts["1"]],
    "4": [posts["2"], posts["1"]],
    "5": [],
}


class Post(BaseModel):
    id: str
    author: str
    title: str
    url: str
    content: str
    ups: str
    downs: str


@app.resolver(type_name="Query", field_name="getPost")
def get_post(id: str = "") -> dict:
    post = Post(**posts[id]).dict()
    return post


@app.resolver(type_name="Query", field_name="allPosts")
def all_posts() -> List[dict]:
    parsed_posts = [post for post in posts.values()]
    return parsed_posts


@app.resolver(type_name="Post", field_name="relatedPosts")
def related_posts() -> List[dict]:
    posts = []
    for resolver_event in app.current_event:
        if resolver_event.source:
            posts.append(posts_related[resolver_event.source["id"]])
    return posts


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
