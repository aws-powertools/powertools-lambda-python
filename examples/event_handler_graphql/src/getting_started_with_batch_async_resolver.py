from typing import Any, List, Optional

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


@app.async_batch_resolver(type_name="Query", field_name="relatedPosts")
async def related_posts(event: List[AppSyncResolverEvent]) -> Optional[List[Any]]:
    results = []

    for record in event:  # (1)!
        post_id = record.arguments.get("post_id")
        try:
            results.append(posts_related[post_id] if post_id else None)
            # Add other logic here
        except Exception:
            logger.error("Error processing record", post_id=post_id)

    return results


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
