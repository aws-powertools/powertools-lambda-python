import pytest

from aws_lambda_powertools.event_handler.async_execution.routes.s3 import S3Route
from aws_lambda_powertools.utilities.data_classes.s3_event import S3Event
from tests.functional.utils import load_event


class TestS3Route:
    def test_constructor_error(self):
        with pytest.raises(ValueError):
            S3Route(func=None)

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without bucket at option_func
            (
                {"func": None, "bucket": "lambda-artifacts-deafc19498e3f2df", "bucket_prefix": "lambda-artifacts-d"},
                {"bucket": None},
                False,
            ),
            # with bucket and bucket_prefix
            # match all
            (
                {"func": None, "bucket": "lambda-artifacts-deafc19498e3f2df", "bucket_prefix": "lambda-artifacts-d"},
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                True,
            ),
            # with bucket and bucket_prefix
            # match 1, unmatch 1
            (
                {"func": None, "bucket": "lambda-artifacts-deafc19498e3f2df", "bucket_prefix": "ambda-artifacts-d"},
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                True,
            ),
            (
                {"func": None, "bucket": "lambda-artifacts-9999999999999999", "bucket_prefix": "lambda-artifacts-d"},
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                False,
            ),
            # with bucket and bucket_prefix
            # unmatch all
            (
                {"func": None, "bucket": "lambda-artifacts-9999999999999999", "bucket_prefix": "ambda-artifacts-d"},
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                False,
            ),
            # with bucket
            (
                {
                    "func": None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                },
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                True,
            ),
            (
                {
                    "func": None,
                    "bucket": "lambda-artifacts-9999999999999999",
                },
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                False,
            ),
            # with bucket_prefix
            (
                {
                    "func": None,
                    "bucket_prefix": "lambda-a",
                },
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                True,
            ),
            (
                {
                    "func": None,
                    "bucket_prefix": "ambda-a",
                },
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                False,
            ),
            # without bucket and bucket_prefix
            (
                {"func": None, "key": "b21b84d653bb07b05b1e6b33684dc11b"},
                {"bucket": "lambda-artifacts-deafc19498e3f2df"},
                False,
            ),
        ],
    )
    def test_is_target_with_bucket(self, option_constructor, option_func, expected):
        route = S3Route(**option_constructor)
        actual = route.is_target_with_bucket(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without key at option_func
            (
                {"func": None, "key": "b21b84d653bb07b05b1e6b33684dc11b", "key_prefix": "b21b", "key_suffix": "c11b"},
                {"key": None},
                False,
            ),
            # without key, key_prefix, and key_suffix
            (
                {"func": None, "bucket": "lambda-artifacts-deafc19498e3f2df"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_prefix, and key_suffix
            # match all
            (
                {"func": None, "key": "b21b84d653bb07b05b1e6b33684dc11b", "key_prefix": "b21b", "key_suffix": "c11b"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            # with key, key_prefix, and key_suffix
            # match 2, unmatch 1
            (
                {"func": None, "key": "b21b84d653bb07b05b1e6b33684dc11b", "key_prefix": "b21b", "key_suffix": "9999"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {"func": None, "key": "b21b84d653bb07b05b1e6b33684dc11b", "key_prefix": "9999", "key_suffix": "c11b"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {"func": None, "key": "99999999999999999999999999999999", "key_prefix": "b21b", "key_suffix": "c11b"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_prefix, and key_suffix
            # match 1, unmatch 2
            (
                {"func": None, "key": "b21b84d653bb07b05b1e6b33684dc11b", "key_prefix": "9999", "key_suffix": "9999"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {"func": None, "key": "99999999999999999999999999999999", "key_prefix": "b21b", "key_suffix": "9999"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            (
                {"func": None, "key": "99999999999999999999999999999999", "key_prefix": "9999", "key_suffix": "c11b"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_prefix, and key_suffix
            # unmatch all
            (
                {"func": None, "key": "99999999999999999999999999999999", "key_prefix": "9999", "key_suffix": "9999"},
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_prefix
            # match all
            (
                {
                    "func": None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "key_prefix": "b21b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            # with key, key_prefix
            # match 1, unmatch 1
            (
                {
                    "func": None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "key_prefix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {
                    "func": None,
                    "key": "99999999999999999999999999999999",
                    "key_prefix": "b21b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_prefix
            # unmatch all
            (
                {
                    "func": None,
                    "key": "99999999999999999999999999999999",
                    "key_prefix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_suffix
            # match all
            (
                {
                    "func": None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "key_suffix": "c11b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            # with key, key_suffix
            # match 1, unmatch 1
            (
                {
                    "func": None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "key_suffix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {
                    "func": None,
                    "key": "99999999999999999999999999999999",
                    "key_suffix": "c11b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key, key_suffix
            # unmatch all
            (
                {
                    "func": None,
                    "key": "99999999999999999999999999999999",
                    "key_suffix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key_prefix, key_suffix
            # match all
            (
                {
                    "func": None,
                    "key_prefix": "b21b",
                    "key_suffix": "c11b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            # with key_prefix, key_suffix
            # match 1, unmatch 1
            (
                {
                    "func": None,
                    "key_prefix": "b21b",
                    "key_suffix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            (
                {
                    "func": None,
                    "key_prefix": "9999",
                    "key_suffix": "c11b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key_prefix, key_suffix
            # unmatch all
            (
                {
                    "func": None,
                    "key_prefix": "9999",
                    "key_suffix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key
            (
                {
                    "func": None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {
                    "func": None,
                    "key": "99999999999999999999999999999999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with key_prefix
            (
                {
                    "func": None,
                    "key_prefix": "b21b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {
                    "func": None,
                    "key_prefix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
            # with_key_suffix
            (
                {
                    "func": None,
                    "key_suffix": "c11b",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                True,
            ),
            (
                {
                    "func": None,
                    "key_suffix": "9999",
                },
                {"key": "b21b84d653bb07b05b1e6b33684dc11b"},
                False,
            ),
        ],
    )
    def test_is_target_with_key(self, option_constructor, option_func, expected):
        route = S3Route(**option_constructor)
        actual = route.is_target_with_key(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without event_name and event_name_prefix
            ({"func": None, "bucket": "lambda-artifacts-deafc19498e3f2df"}, {"event_name": "ObjectCreated:Put"}, False),
            # without event_name at option_func
            (
                {"func": None, "event_name": "ObjectCreated:Put", "event_name_prefix": "ObjectCreated:"},
                {"event_name": None},
                False,
            ),
            # with event_name and event_name_prefix
            # match all
            (
                {"func": None, "event_name": "ObjectCreated:Put", "event_name_prefix": "ObjectCreated:"},
                {"event_name": "ObjectCreated:Put"},
                True,
            ),
            # with event_name and event_name_prefix
            # match 1, unmatch 1
            (
                {"func": None, "event_name": "ObjectCreated:Put", "event_name_prefix": "bjectCreated:"},
                {"event_name": "ObjectCreated:Put"},
                True,
            ),
            (
                {"func": None, "event_name": "ObjectCreated:PutV2", "event_name_prefix": "ObjectCreated:"},
                {"event_name": "ObjectCreated:Put"},
                False,
            ),
            # with event_name and event_name_prefix
            # unmatch all
            (
                {"func": None, "event_name": "ObjectCreated:PutV2", "event_name_prefix": "bjectCreated:"},
                {"event_name": "ObjectCreated:Put"},
                False,
            ),
            # with event_name
            (
                {
                    "func": None,
                    "event_name": "ObjectCreated:Put",
                },
                {"event_name": "ObjectCreated:Put"},
                True,
            ),
            (
                {
                    "func": None,
                    "event_name": "ObjectCreated:PutV2",
                },
                {"event_name": "ObjectCreated:Put"},
                False,
            ),
            # with event_name_prefix
            (
                {
                    "func": None,
                    "event_name_prefix": "ObjectCreated:",
                },
                {"event_name": "ObjectCreated:Put"},
                True,
            ),
            (
                {
                    "func": None,
                    "event_name_prefix": "bjectCreated:",
                },
                {"event_name": "ObjectCreated:Put"},
                False,
            ),
        ],
    )
    def test_is_target_with_event_name(self, option_constructor, option_func, expected):
        route = S3Route(**option_constructor)
        actual = route.is_target_with_event_name(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "option_constructor, option_func, expected",
        [
            # without configuration_id and configuration_id_prefix
            (
                {"func": None, "bucket": "lambda-artifacts-deafc19498e3f2df"},
                {"configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1"},
                False,
            ),
            # without configuration_id at option_func
            (
                {
                    "func": None,
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                    "configuration_id_prefix": "828aa6fc-f",
                },
                {"configuration_id": None},
                False,
            ),
            # with configuration_id and configuration_id_prefix
            # match all
            (
                {
                    "func": None,
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                    "configuration_id_prefix": "828aa6fc-f",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with configuration_id and configuration_id_prefix
            # match 1, unmatch 1
            (
                {
                    "func": None,
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                    "configuration_id_prefix": "28aa6fc-f",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            (
                {
                    "func": None,
                    "configuration_id": "99999999-9999-9999-9999-999999999999",
                    "configuration_id_prefix": "828aa6fc-f",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with configuration_id and configuration_id_prefix
            # unmatch all
            (
                {
                    "func": None,
                    "configuration_id": "99999999-9999-9999-9999-999999999999",
                    "configuration_id_prefix": "28aa6fc-f",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with configuration_id
            (
                {
                    "func": None,
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            (
                {
                    "func": None,
                    "configuration_id": "99999999-9999-9999-9999-999999999999",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with configuration_id_prefix
            (
                {
                    "func": None,
                    "configuration_id_prefix": "828aa6fc-f",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            (
                {
                    "func": None,
                    "configuration_id_prefix": "28aa6fc-f",
                },
                {
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
        ],
    )
    def test_is_target_with_configuration_id(self, option_constructor, option_func, expected):
        route = S3Route(**option_constructor)
        actual = route.is_target_with_configuration_id(**option_func)
        assert actual == expected

    @pytest.mark.parametrize(
        "event_name, option_constructor, is_match",
        [
            # with bucket, key, event_name, and configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with bucket, key, event_name, and configuration_id
            # match 3, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket, key, event_name, and configuration_id
            # match 2, unmatch 2
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket, key, event_name, and configuration_id
            # match 1, unmatch 3
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket, key, event_name, and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with bucket, key, and event_name
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                },
                True,
            ),
            # with bucket, key, and event_name
            # match 2, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                },
                False,
            ),
            # with bucket, key, and event_name
            # match 1, unmatch 2
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                },
                False,
            ),
            # with bucket, key, and event_name
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            # with bucket, key, and configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with bucket, key, and configuration_id
            # match 2, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket, key, and configuration_id
            # match 1, unmatch 2
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with bucket, key, and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with bucket, event_name, and configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with bucket, event_name, and configuration_id
            # match 2, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket, event_name, and configuration_id
            # match 1, unmatch 2
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket, event_name, and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with key, event_name, configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with key, event_name, configuration_id
            # match 2, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with key, event_name, configuration_id
            # match 1, unmatch 2
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with key, event_name, and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with bucket and key
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                },
                True,
            ),
            # with bucket and key
            # match 1, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "key": "99999999999999999999999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                },
                False,
            ),
            # with bucket and key
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "key": "99999999999999999999999999999999",
                },
                False,
            ),
            # with bucket and event_name
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "event_name": "ObjectCreated:Put",
                },
                True,
            ),
            # with bucket and event_name
            # match 1, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "event_name": "ObjectCreated:Put",
                },
                False,
            ),
            # with bucket and event_name
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            # with bucket and configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with bucket and configuration_id
            # match 1, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with bucket and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with key and event_name
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:Put",
                },
                True,
            ),
            # with key and event_name
            # match 1, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:Put",
                },
                False,
            ),
            # with key and event_name
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            # with key and configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with key and configuration_id
            # match 1, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with key and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with event_name and configuration_id
            # match all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                True,
            ),
            # with event_name and configuration_id
            # match 1, unmatch 1
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "event_name": "ObjectCreated:Put",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1",
                },
                False,
            ),
            # with event_name and configuration_id
            # unmatch all
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "event_name": "ObjectCreated:PutV2",
                    "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999",
                },
                False,
            ),
            # with bucket
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-deafc19498e3f2df",
                },
                True,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "bucket": "lambda-artifacts-9999999999999999",
                },
                False,
            ),
            # with key
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "b21b84d653bb07b05b1e6b33684dc11b",
                },
                True,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "key": "99999999999999999999999999999999",
                },
                False,
            ),
            # with event_name
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "event_name": "ObjectCreated:Put",
                },
                True,
            ),
            (
                "s3Event.json",
                {
                    "func": lambda *_: None,
                    "event_name": "ObjectCreated:PutV2",
                },
                False,
            ),
            # with configuration_id
            (
                "s3Event.json",
                {"func": lambda *_: None, "configuration_id": "828aa6fc-f7b5-4305-8584-487c791949c1"},
                True,
            ),
            (
                "s3Event.json",
                {"func": lambda *_: None, "configuration_id": "828aa6fc-f7b5-4305-8584-999999999999"},
                False,
            ),
        ],
    )
    def test_match_for_s3_event(self, event_name, option_constructor, is_match):
        event = load_event(file_name=event_name)
        route = S3Route(**option_constructor)
        actual = route.match(event=event)
        if is_match:
            expected = route.func, S3Event(event)
            assert actual == expected
        else:
            assert actual is None

    @pytest.mark.parametrize(
        "event_name",
        [
            "activeMQEvent.json",
            "albEvent.json",
            "albEventPathTrailingSlash.json",
            "albMultiValueHeadersEvent.json",
            "albMultiValueQueryStringEvent.json",
            "apiGatewayAuthorizerRequestEvent.json",
            "apiGatewayAuthorizerTokenEvent.json",
            "apiGatewayAuthorizerV2Event.json",
            "apiGatewayProxyEvent.json",
            "apiGatewayProxyEventAnotherPath.json",
            "apiGatewayProxyEventNoOrigin.json",
            "apiGatewayProxyEventPathTrailingSlash.json",
            "apiGatewayProxyEventPrincipalId.json",
            "apiGatewayProxyEvent_noVersionAuth.json",
            "apiGatewayProxyOtherEvent.json",
            "apiGatewayProxyV2Event.json",
            "apiGatewayProxyV2EventPathTrailingSlash.json",
            "apiGatewayProxyV2Event_GET.json",
            "apiGatewayProxyV2IamEvent.json",
            "apiGatewayProxyV2LambdaAuthorizerEvent.json",
            "apiGatewayProxyV2OtherGetEvent.json",
            "apiGatewayProxyV2SchemaMiddlwareInvalidEvent.json",
            "apiGatewayProxyV2SchemaMiddlwareValidEvent.json",
            "apigatewayeSchemaMiddlwareInvalidEvent.json",
            "apigatewayeSchemaMiddlwareValidEvent.json",
            "appSyncAuthorizerEvent.json",
            "appSyncAuthorizerResponse.json",
            "appSyncBatchEvent.json",
            "appSyncDirectResolver.json",
            "appSyncResolverEvent.json",
            "awsConfigRuleConfigurationChanged.json",
            "awsConfigRuleOversizedConfiguration.json",
            "awsConfigRuleScheduled.json",
            "bedrockAgentEvent.json",
            "bedrockAgentEventWithPathParams.json",
            "bedrockAgentPostEvent.json",
            "cloudWatchAlarmEventCompositeMetric.json",
            "cloudWatchAlarmEventSingleMetric.json",
            "cloudWatchDashboardEvent.json",
            "cloudWatchLogEvent.json",
            "cloudWatchLogEventWithPolicyLevel.json",
            "cloudformationCustomResourceCreate.json",
            "cloudformationCustomResourceDelete.json",
            "cloudformationCustomResourceUpdate.json",
            "codeDeployLifecycleHookEvent.json",
            "codePipelineEvent.json",
            "codePipelineEventData.json",
            "codePipelineEventEmptyUserParameters.json",
            "codePipelineEventWithEncryptionKey.json",
            "cognitoCreateAuthChallengeEvent.json",
            "cognitoCustomEmailSenderEvent.json",
            "cognitoCustomMessageEvent.json",
            "cognitoCustomSMSSenderEvent.json",
            "cognitoDefineAuthChallengeEvent.json",
            "cognitoPostAuthenticationEvent.json",
            "cognitoPostConfirmationEvent.json",
            "cognitoPreAuthenticationEvent.json",
            "cognitoPreSignUpEvent.json",
            "cognitoPreTokenGenerationEvent.json",
            "cognitoPreTokenV2GenerationEvent.json",
            "cognitoUserMigrationEvent.json",
            "cognitoVerifyAuthChallengeResponseEvent.json",
            "connectContactFlowEventAll.json",
            "connectContactFlowEventMin.json",
            "dynamoStreamEvent.json",
            "eventBridgeEvent.json",
            "kafkaEventMsk.json",
            "kafkaEventSelfManaged.json",
            "kinesisFirehoseKinesisEvent.json",
            "kinesisFirehosePutEvent.json",
            "kinesisFirehoseSQSEvent.json",
            "kinesisStreamCloudWatchLogsEvent.json",
            "kinesisStreamEvent.json",
            "kinesisStreamEventOneRecord.json",
            "lambdaFunctionUrlEvent.json",
            "lambdaFunctionUrlEventPathTrailingSlash.json",
            "lambdaFunctionUrlEventWithHeaders.json",
            "lambdaFunctionUrlIAMEvent.json",
            "rabbitMQEvent.json",
            "s3BatchOperationEventSchemaV1.json",
            "s3BatchOperationEventSchemaV2.json",
            "s3EventBridgeNotificationObjectCreatedEvent.json",
            "s3EventBridgeNotificationObjectDeletedEvent.json",
            "s3EventBridgeNotificationObjectExpiredEvent.json",
            "s3EventBridgeNotificationObjectRestoreCompletedEvent.json",
            "s3ObjectEventIAMUser.json",
            "s3ObjectEventTempCredentials.json",
            "s3SqsEvent.json",
            "secretsManagerEvent.json",
            "sesEvent.json",
            "snsEvent.json",
            "snsSqsEvent.json",
            "snsSqsFifoEvent.json",
            "sqsDlqTriggerEvent.json",
            "sqsEvent.json",
            "vpcLatticeEvent.json",
            "vpcLatticeEventPathTrailingSlash.json",
            "vpcLatticeEventV2PathTrailingSlash.json",
            "vpcLatticeV2Event.json",
            "vpcLatticeV2EventWithHeaders.json",
        ],
    )
    def test_match_for_not_s3_event(self, event_name):
        event = load_event(file_name=event_name)
        route = S3Route(func=None, bucket="lambda-artifacts-deafc19498e3f2df")
        actual = route.match(event=event)
        assert actual is None
