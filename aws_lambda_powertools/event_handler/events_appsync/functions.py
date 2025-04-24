from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

PATH_REGEX = re.compile(r"^\/([^\/\*]+)(\/[^\/\*]+)*(\/\*)?$")


def is_valid_path(path: str) -> bool:
    """
    Checks if a given path is valid based on specific rules.

    Parameters
    ----------
    path: str
        The path to validate

    Returns:
    --------
    bool:
        True if the path is valid, False otherwise

    Examples:
        >>> is_valid_path('/*')
        True
        >>> is_valid_path('/users')
        True
        >>> is_valid_path('/users/profile')
        True
        >>> is_valid_path('/users/*/details')
        False
        >>> is_valid_path('/users/*')
        True
        >>> is_valid_path('users')
        False
    """
    return True if path == "/*" else bool(PATH_REGEX.fullmatch(path))


def find_best_route(routes: dict[str, Any], path: str):
    """
    Find the most specific matching route for a given path.

    Examples of matches:
        Route: /default/v1/*         Path: /default/v1/users      -> MATCH
        Route: /default/v1/*         Path: /default/v1/users/students  -> MATCH
        Route: /default/v1/users/*   Path: /default/v1/users/123  -> MATCH (this wins over /default/v1/*)
        Route: /*                    Path: /anything/here      -> MATCH (lowest priority)

    Parameters
    ----------
    routes: dict[str, Any]
        Dictionary containing routes and their handlers
            Format: {
                'resolvers': {
                    '/path/*': {'func': callable, 'aggregate': bool},
                    '/path/specific/*': {'func': callable, 'aggregate': bool}
                }
            }
    path: str
        Actual path to match (e.g., '/default/v1/users')

    Returns
    -------
        str: Most specific matching route or None if no match
    """

    @lru_cache(maxsize=1024)
    def pattern_to_regex(route):
        """
        Convert a route pattern to a regex pattern with caching.
        Examples:
            /default/v1/*         -> ^/default/v1/[^/]+$
            /default/v1/users/*   -> ^/default/v1/users/.*$

        Parameters
        ----------
        route: str
            Route pattern with wildcards

        Returns
        -------
        Pattern:
            Compiled regex pattern
        """
        # Escape special regex chars but convert * to regex pattern
        pattern = re.escape(route).replace("\\*", "[^/]+")

        # If pattern ends with [^/]+, replace with .* for multi-segment match
        if pattern.endswith("[^/]+"):
            pattern = pattern[:-6] + ".*"

        # Compile and return the regex pattern
        return re.compile(f"^{pattern}$")

    # Find all matching routes
    matches = [route for route in routes.keys() if pattern_to_regex(route).match(path)]

    # Return the most specific route (longest length minus wildcards)
    # Examples of specificity:
    # - '/default/v1/users'     -> score: 14 (len=14, wildcards=0)
    # - '/default/v1/users/*'   -> score: 14 (len=15, wildcards=1)
    # - '/default/v1/*'        -> score: 8  (len=9, wildcards=1)
    # - '/*'               -> score: 0  (len=2, wildcards=1)
    return max(matches, key=lambda x: len(x) - x.count("*"), default=None)
