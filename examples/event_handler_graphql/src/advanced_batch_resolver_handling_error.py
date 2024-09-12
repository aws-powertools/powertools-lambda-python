from typing import Any, Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = AppSyncResolver()


posts_related = {
    "1": {"title": "post1"},
    "2": {"title": "post2"},
    "3": {"title": "post3"},
}


@app.batch_resolver(type_name="Query", field_name="relatedPosts", aggregate=False, raise_on_error=True)  # (1)!
def related_posts(event: AppSyncResolverEvent, post_id: str = "") -> Dict[str, Any]:
    return posts_related[post_id]


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
