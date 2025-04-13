import pytest

from aws_lambda_powertools.event_handler.events_appsync.functions import find_best_route, is_valid_path


@pytest.mark.parametrize(
    "path,expected,description",
    [
        ("/*", True, "Root wildcard path is valid"),
        ("/users", True, "Simple path with one segment is valid"),
        ("/users/profile/settings", True, "Path with multiple segments is valid"),
        ("/users/*", True, "Path ending with /* is valid"),
        ("/users/*/details", False, "Path with wildcard in the middle is invalid"),
        ("users/profile", False, "Path without leading slash is invalid"),
        ("/users/", False, "Path with trailing slash is invalid"),
        ("", False, "Empty path is invalid"),
        ("/", False, "Root path / is invalid according to the regex"),
    ],
)
def test_path_validation(path, expected, description):
    """Test various path validation scenarios."""
    # Given a path (provided by parametrize)

    # When validating
    result = is_valid_path(path)

    # Then must match the regexp
    assert result is expected, description


def test_path_with_non_string_input():
    """Test that non-string input raises an appropriate error."""
    # Given
    path = None

    # When/Then
    with pytest.raises(TypeError):
        is_valid_path(path)


@pytest.mark.parametrize(
    "routes, path, expected_route, description",
    [
        (
            {
                "/default/v1/*": {"func": lambda x: x, "aggregate": False},
                "/default/v1/users/*": {"func": lambda x: x, "aggregate": False},
                "/default/v1/users/active/*": {"func": lambda x: x, "aggregate": False},
            },
            "/default/v1/users/active/123",
            "/default/v1/users/active/*",
            "Most specific route with wildcard should be matched",
        ),
    ],
)
def test_find_best_route_specific_wildcard(routes, path, expected_route, description):
    """Test that find_best_route selects most specific wildcard path."""
    # GIVEN

    # WHEN
    result = find_best_route(routes, path)

    # THEN
    assert result == expected_route, description


@pytest.mark.parametrize(
    "routes, path, expected_route, description",
    [
        (
            {
                "/default/v1/users": {"func": lambda x: x, "aggregate": False},
                "/default/v1/*": {"func": lambda x: x, "aggregate": False},
            },
            "/default/v1/users",
            "/default/v1/users",
            "Exact match wins over wildcard match",
        ),
    ],
)
def test_find_best_route_exact_match(routes, path, expected_route, description):
    """Test that find_best_route prefers exact matches over wildcard matches."""
    # GIVEN

    # WHEN
    result = find_best_route(routes, path)

    # THEN
    assert result == expected_route, description


@pytest.mark.parametrize(
    "routes, path, expected_route, description",
    [
        (
            {
                "/*": {"func": lambda x: x, "aggregate": False},
                "/other/*": {"func": lambda x: x, "aggregate": False},
            },
            "/default/v1/users",
            "/*",
            "Fallback to /* when no specific matches",
        ),
    ],
)
def test_find_best_route_fallback(routes, path, expected_route, description):
    """Test that find_best_route falls back to /* when no specific route matches."""
    # GIVEN

    # WHEN
    result = find_best_route(routes, path)

    # THEN
    assert result == expected_route, description


@pytest.mark.parametrize(
    "routes, path, expected_route, description",
    [
        (
            {
                "/api/v1/users/*": {"func": lambda x: x, "aggregate": False},
                "/api/v1/posts/*": {"func": lambda x: x, "aggregate": False},
            },
            "/api/v2/users/123",
            None,
            "No match should return None",
        ),
        (
            {},
            "/any/path",
            None,
            "Empty routes dictionary should return None",
        ),
    ],
)
def test_find_best_route_no_match(routes, path, expected_route, description):
    """Test that find_best_route returns None when no routes match."""
    # GIVEN

    # WHEN
    result = find_best_route(routes, path)

    # THEN
    assert result == expected_route, description
