from datetime import datetime

from aws_lambda_powertools.shared.cookies import Cookie, SameSite


def test_cookie_without_secure():
    # GIVEN a cookie without secure
    cookie = Cookie(name="powertools", value="test", path="/", secure=False)

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.secure is False
    assert str(cookie) == "powertools=test; Path=/"


def test_cookie_with_path():
    # GIVEN a cookie with a path
    cookie = Cookie(name="powertools", value="test", path="/")

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert str(cookie) == "powertools=test; Path=/; Secure"


def test_cookie_with_domain():
    # GIVEN a cookie with a domain
    cookie = Cookie(name="powertools", value="test", path="/", domain="example.com")

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert cookie.domain == "example.com"
    assert str(cookie) == "powertools=test; Path=/; Domain=example.com; Secure"


def test_cookie_with_expires():
    # GIVEN a cookie with a expires
    time_to_expire = datetime(year=2022, month=12, day=31)
    cookie = Cookie(name="powertools", value="test", path="/", expires=time_to_expire)

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert cookie.expires == time_to_expire
    assert str(cookie) == "powertools=test; Path=/; Expires=Sat, 31 Dec 2022 00:00:00 GMT; Secure"


def test_cookie_with_max_age_positive():
    # GIVEN a cookie with a positive max age
    cookie = Cookie(name="powertools", value="test", path="/", max_age=100)

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert cookie.max_age == 100
    assert str(cookie) == "powertools=test; Path=/; Max-Age=100; Secure"


def test_cookie_with_max_age_negative():
    # GIVEN a cookie with a negative max age
    cookie = Cookie(name="powertools", value="test", path="/", max_age=-100)

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value and Max-Age must be 0
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert str(cookie) == "powertools=test; Path=/; Max-Age=0; Secure"


def test_cookie_with_http_only():
    # GIVEN a cookie with http_only
    cookie = Cookie(name="powertools", value="test", path="/", http_only=True)

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert cookie.http_only is True
    assert str(cookie) == "powertools=test; Path=/; HttpOnly; Secure"


def test_cookie_with_same_site():
    # GIVEN a cookie with same_site
    cookie = Cookie(name="powertools", value="test", path="/", same_site=SameSite.STRICT_MODE)

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert cookie.same_site == SameSite.STRICT_MODE
    assert str(cookie) == "powertools=test; Path=/; Secure; SameSite=Strict"


def test_cookie_with_custom_attribute():
    # GIVEN a cookie with custom_attributes
    cookie = Cookie(name="powertools", value="test", path="/", custom_attributes=["extra1=value1", "extra2=value2"])

    # WHEN getting the cookie's attributes
    # THEN the path attribute should be set to the provided value
    assert cookie.name == "powertools"
    assert cookie.value == "test"
    assert cookie.path == "/"
    assert cookie.custom_attributes == ["extra1=value1", "extra2=value2"]
    assert str(cookie) == "powertools=test; Path=/; Secure; extra1=value1; extra2=value2"
