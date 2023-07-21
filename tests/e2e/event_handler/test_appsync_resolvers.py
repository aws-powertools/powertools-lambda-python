import json

import pytest
from requests import Request

from tests.e2e.utils import data_fetcher


@pytest.fixture
def appsync_endpoint(infrastructure: dict) -> str:
    return infrastructure["GraphQLHTTPUrl"]


@pytest.fixture
def appsync_access_key(infrastructure: dict) -> str:
    return infrastructure["GraphQLAPIKey"]


@pytest.mark.xdist_group(name="event_handler")
def test_appsync_get_all_posts(appsync_endpoint, appsync_access_key):
    # GIVEN
    body = {
        "query": "query MyQuery { allPosts { post_id }}",
        "variables": None,
        "operationName": "MyQuery",
    }

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=appsync_endpoint,
            json=body,
            headers={"x-api-key": appsync_access_key, "Content-Type": "application/json"},
        ),
    )

    # THEN expect a HTTP 200 response and content return list of Posts
    assert response.status_code == 200
    assert response.content is not None

    data = json.loads(response.content.decode("ascii"))["data"]

    assert data["allPosts"] is not None
    assert len(data["allPosts"]) > 0


@pytest.mark.xdist_group(name="event_handler")
def test_appsync_get_post(appsync_endpoint, appsync_access_key):
    # GIVEN
    post_id = "1"
    body = {
        "query": f'query MyQuery {{ getPost(post_id: "{post_id}") {{ post_id }} }}',
        "variables": None,
        "operationName": "MyQuery",
    }

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=appsync_endpoint,
            json=body,
            headers={"x-api-key": appsync_access_key, "Content-Type": "application/json"},
        ),
    )

    # THEN expect a HTTP 200 response and content return Post id
    assert response.status_code == 200
    assert response.content is not None

    data = json.loads(response.content.decode("ascii"))["data"]

    assert data["getPost"]["post_id"] == post_id


@pytest.mark.xdist_group(name="event_handler")
def test_appsync_get_related_posts_batch(appsync_endpoint, appsync_access_key):
    # GIVEN
    post_id = "2"
    related_posts_ids = ["3", "5"]

    body = {
        "query": f'query MyQuery {{ getPost(post_id: "{post_id}") \
              {{ post_id relatedPosts {{ post_id }} relatedPostsAsync {{ post_id }} }} }}',
        "variables": None,
        "operationName": "MyQuery",
    }

    # WHEN
    response = data_fetcher.get_http_response(
        Request(
            method="POST",
            url=appsync_endpoint,
            json=body,
            headers={"x-api-key": appsync_access_key, "Content-Type": "application/json"},
        ),
    )

    # THEN expect a HTTP 200 response and content return Post id with dependent Posts id's
    assert response.status_code == 200
    assert response.content is not None

    data = json.loads(response.content.decode("ascii"))["data"]

    assert data["getPost"]["post_id"] == post_id
    assert len(data["getPost"]["relatedPosts"]) == len(related_posts_ids)
    assert len(data["getPost"]["relatedPostsAsync"]) == len(related_posts_ids)
    for post in data["getPost"]["relatedPosts"]:
        assert post["post_id"] in related_posts_ids
    for post in data["getPost"]["relatedPostsAsync"]:
        assert post["post_id"] in related_posts_ids
