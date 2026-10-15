import pytest

from aws_lambda_powertools.event_handler.events_appsync.functions import find_best_route


@pytest.mark.parametrize(
    "path, expected_route",
    [
        ("/default/users/123", "/default/users/*"),
        ("/default/users/123/profile", "/default/users/*"),
        ("/default/usersettings", "/default/*"),
        ("/default/users-archive/1", "/default/*"),
        ("/other/channel", "/*"),
    ],
)
def test_find_best_route_wildcard_matches_whole_segments(path, expected_route):
    # GIVEN routes where a more specific route shares a string prefix with sibling channels
    routes = {
        "/*": {"func": lambda x: x, "aggregate": False},
        "/default/*": {"func": lambda x: x, "aggregate": False},
        "/default/users/*": {"func": lambda x: x, "aggregate": False},
    }

    # WHEN finding the best route
    result = find_best_route(routes, path)

    # THEN the wildcard only matches whole path segments
    assert result == expected_route
