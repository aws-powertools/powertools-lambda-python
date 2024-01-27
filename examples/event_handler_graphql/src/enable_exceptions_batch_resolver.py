from typing import Dict, Optional

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncResolver(raise_error_on_failed_batch=True)  # (1)!


posts_related = {
    "1": {"title": "post1"},
    "2": {"title": "post2"},
    "3": {"title": "post3"},
}


class PostRelatedNotFound(Exception):
    ...


@app.batch_resolver(type_name="Query", field_name="relatedPosts")
def related_posts(event: AppSyncResolverEvent, post_id: str) -> Optional[Dict]:
    post_found = posts_related.get(post_id, None)

    if not post_found:
        raise PostRelatedNotFound(f"Unable to find a related post with ID {post_id}.")

    return post_found


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
