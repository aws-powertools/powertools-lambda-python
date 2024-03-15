from typing import Dict, Optional

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncResolver()


posts_related = {
    "1": {"title": "post1"},
    "2": {"title": "post2"},
    "3": {"title": "post3"},
}


@app.async_batch_resolver(type_name="Query", field_name="relatedPosts")
async def related_posts(event: AppSyncResolverEvent, post_id: str) -> Optional[Dict]:
    return posts_related.get(post_id, None)


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
