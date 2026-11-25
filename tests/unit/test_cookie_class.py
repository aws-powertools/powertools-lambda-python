from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

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


def test_cookie_with_expires_in_another_timezone():
    # GIVEN a cookie that expires at 12:00 in UTC+2, which is 10:00 UTC
    time_to_expire = datetime(2026, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))
    cookie = Cookie(name="powertools", value="test", path="/", expires=time_to_expire)

    # WHEN getting the cookie's attributes
    # THEN Expires should be the same instant in GMT
    assert str(cookie) == "powertools=test; Path=/; Expires=Thu, 01 Jan 2026 10:00:00 GMT; Secure"


def test_cookie_with_expires_and_non_english_locale():
    # GIVEN an expiry datetime whose strftime names days and months in German, like after
    # locale.setlocale(locale.LC_TIME, "de_DE.UTF-8"), without needing that locale installed
    class GermanLocaleDatetime(datetime):
        def strftime(self, fmt):
            return super().strftime(fmt.replace("%a", "Fr.").replace("%b", "Okt."))

    cookie = Cookie(name="powertools", value="test", path="/", expires=GermanLocaleDatetime(2026, 10, 30, 7, 28))

    # WHEN getting the cookie's attributes
    # THEN Expires should use the English day and month names browsers can parse
    assert str(cookie) == "powertools=test; Path=/; Expires=Fri, 30 Oct 2026 07:28:00 GMT; Secure"


def test_cookie_with_expires_date():
    # GIVEN a cookie that expires on a date rather than a datetime
    cookie = Cookie(name="powertools", value="test", path="/", expires=date(2026, 1, 1))

    # WHEN getting the cookie's attributes
    # THEN Expires should be midnight GMT of that date
    assert str(cookie) == "powertools=test; Path=/; Expires=Thu, 01 Jan 2026 00:00:00 GMT; Secure"


@pytest.mark.parametrize(
    "time_to_expire, expected",
    [
        pytest.param(
            datetime.max.replace(tzinfo=timezone(timedelta(hours=-5))),
            "Fri, 31 Dec 9999 23:59:59 GMT",
            id="after year 9999 in UTC",
        ),
        pytest.param(
            datetime.min.replace(tzinfo=timezone(timedelta(hours=5))),
            "Mon, 01 Jan 0001 00:00:00 GMT",
            id="before year 1 in UTC",
        ),
    ],
)
def test_cookie_with_expires_outside_years_1_to_9999_in_utc(time_to_expire, expected):
    # GIVEN a cookie whose expiry is an instant that UTC cannot represent
    cookie = Cookie(name="powertools", value="test", path="/", expires=time_to_expire)

    # WHEN getting the cookie's attributes
    # THEN Expires should be the closest date that can be written, without raising
    assert str(cookie) == f"powertools=test; Path=/; Expires={expected}; Secure"


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


def test_cookie_with_max_age_zero():
    # GIVEN a cookie with a zero max age
    cookie = Cookie(name="powertools", value="test", path="/", max_age=0)

    # WHEN getting the cookie's attributes
    # THEN Max-Age must be 0 so the browser deletes the cookie
    assert cookie.max_age == 0
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


def test_cookie_with_same_site_default_mode():
    # GIVEN a cookie with the default same_site mode
    cookie = Cookie(name="powertools", value="test", path="/", same_site=SameSite.DEFAULT_MODE)

    # WHEN getting the cookie's attributes
    # THEN the SameSite attribute should be left out instead of sent without a value
    assert cookie.same_site == SameSite.DEFAULT_MODE
    assert str(cookie) == "powertools=test; Path=/; Secure"


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
