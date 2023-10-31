from typing import List, Optional

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncResolver()


posts = {
    "1": {
        "post_id": "1",
        "title": "First book",
        "author": "Author1",
        "url": "https://amazon.com/",
        "content": "SAMPLE TEXT AUTHOR 1",
        "ups": "100",
        "downs": "10",
    },
    "2": {
        "post_id": "2",
        "title": "Second book",
        "author": "Author2",
        "url": "https://amazon.com",
        "content": "SAMPLE TEXT AUTHOR 2",
        "ups": "100",
        "downs": "10",
    },
    "3": {
        "post_id": "3",
        "title": "Third book",
        "author": "Author3",
        "url": None,
        "content": None,
        "ups": None,
        "downs": None,
    },
    "4": {
        "post_id": "4",
        "title": "Fourth book",
        "author": "Author4",
        "url": "https://www.amazon.com/",
        "content": "SAMPLE TEXT AUTHOR 4",
        "ups": "1000",
        "downs": "0",
    },
    "5": {
        "post_id": "5",
        "title": "Fifth book",
        "author": "Author5",
        "url": "https://www.amazon.com/",
        "content": "SAMPLE TEXT AUTHOR 5",
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
    post_id: str
    author: str
    title: str
    url: str
    content: str
    ups: str
    downs: str


@app.resolver(type_name="Query", field_name="getPost")
def get_post(post_id: str = "") -> dict:
    post = Post(**posts[post_id]).dict()
    return post


@app.resolver(type_name="Query", field_name="allPosts")
def all_posts() -> List[dict]:
    return list(posts.values())


@app.batch_async_resolver(type_name="Post", field_name="relatedPosts")
async def related_posts_async(event: AppSyncResolverEvent) -> Optional[list]:
    return posts_related[event.source["post_id"]] if event.source else None


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
