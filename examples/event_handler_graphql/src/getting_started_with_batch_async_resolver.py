from __future__ import annotations

from typing import Any

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncResolver()

# mimic DB data for simplicity
posts_related = {
    "1": {"title": "post1"},
    "2": {"title": "post2"},
    "3": {"title": "post3"},
}


async def search_batch_posts(posts: list) -> dict[str, Any]:
    return {post_id: posts_related.get(post_id) for post_id in posts}


@app.async_batch_resolver(type_name="Query", field_name="relatedPosts")
async def related_posts(event: list[AppSyncResolverEvent]) -> list[Any]:  # (1)!
    # Extract all post_ids in order
    post_ids: list = [record.source.get("post_id") for record in event]  # (2)!

    # Get unique post_ids while preserving order
    unique_post_ids = list(dict.fromkeys(post_ids))

    # Fetch posts in a single batch operation
    fetched_posts = await search_batch_posts(unique_post_ids)

    # Return results in original order
    return [fetched_posts.get(post_id) for post_id in post_ids]


def lambda_handler(event, context: LambdaContext) -> dict:
    return app.resolve(event, context)
