from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.s3_event import S3Event

from .base import BaseRoute


class S3Route(BaseRoute):
    bucket: str | None
    bucket_prefix: str | None
    key: str | None
    key_prefix: str | None
    key_suffix: str | None
    event_name: str | None
    event_name_prefix: str | None
    configuration_id: str | None
    configuration_id_prefix: str | None

    def __init__(
        self,
        func: Callable,
        bucket: str | None = None,
        bucket_prefix: str | None = None,
        key: str | None = None,
        key_prefix: str | None = None,
        key_suffix: str | None = None,
        event_name: str | None = None,
        event_name_prefix: str | None = None,
        configuration_id: str | None = None,
        configuration_id_prefix: str | None = None,
    ):
        self.func = func
        self.bucket = bucket
        self.bucket_prefix = bucket_prefix
        self.key = key
        self.key_prefix = key_prefix
        self.key_suffix = key_suffix
        self.event_name = event_name
        self.event_name_prefix = event_name_prefix
        self.configuration_id = configuration_id
        self.configuration_id_prefix = configuration_id_prefix

        if (
            not self.bucket
            and not self.bucket_prefix
            and not self.key
            and not self.key_prefix
            and not self.key_suffix
            and not self.event_name
            and not self.event_name_prefix
            and not self.configuration_id
            and not self.configuration_id_prefix
        ):
            raise ValueError(
                (
                    "bucket, bucket_prefix, key, key_prefix, key_suffix, event_name, event_name_prefix, "
                    "configuration_id, or configuration_id_prefix must be not null"
                ),
            )

    def is_target_with_bucket(self, bucket: str | None) -> bool:
        if not bucket:
            return False
        elif self.bucket:
            return self.bucket == bucket
        elif self.bucket_prefix:
            return bucket.find(self.bucket_prefix) == 0
        else:
            return False

    def is_target_with_key(self, key: str | None) -> bool:
        if not key:
            return False
        elif self.key:
            return self.key == key
        elif self.key_prefix and not self.key_suffix:
            return key.find(self.key_prefix) == 0
        elif not self.key_prefix and self.key_suffix:
            length_suffix = len(self.key_suffix)
            suffix = key[-length_suffix:]
            return self.key_suffix == suffix
        elif self.key_prefix and self.key_suffix:
            length_suffix = len(self.key_suffix)
            suffix = key[-length_suffix:]
            return key.find(self.key_prefix) == 0 and self.key_suffix == suffix
        else:
            return False

    def is_target_with_event_name(self, event_name: str | None) -> bool:
        if not event_name:
            return False
        elif self.event_name:
            return self.event_name == event_name
        elif self.event_name_prefix:
            return event_name.find(self.event_name_prefix) == 0
        else:
            return False

    def is_target_with_configuration_id(self, configuration_id: str | None) -> bool:
        if not configuration_id:
            return False
        elif self.configuration_id:
            return self.configuration_id == configuration_id
        elif self.configuration_id_prefix:
            return configuration_id.find(self.configuration_id_prefix) == 0
        else:
            return False

    def is_target(
        self,
        bucket: str | None,
        key: str | None,
        event_name: str | None,
        configuration_id: str | None,
    ) -> bool:
        flag_bucket = self.is_target_with_bucket(bucket=bucket)
        flag_key = self.is_target_with_key(key=key)
        flag_event_name = self.is_target_with_event_name(event_name=event_name)
        flag_configuration_id = self.is_target_with_configuration_id(configuration_id=configuration_id)

        text = ", ".join(
            [
                "bucket: x" if bucket is None else "bucket: o",
                "key: x" if key is None else "key: o",
                "event_name: x" if event_name is None else "event_name: o",
                "configuration_id: x" if configuration_id is None else "configuration_id: o",
            ],
        )

        mapping = {
            "bucket: o, key: o, event_name: o, configuration_id: o": flag_bucket
            and flag_key
            and flag_event_name
            and flag_configuration_id,
            "bucket: o, key: o, event_name: o, configuration_id: x": flag_bucket and flag_key and flag_event_name,
            "bucket: o, key: o, event_name: x, configuration_id: o": flag_bucket and flag_key and flag_configuration_id,
            "bucket: o, key: x, event_name: o, configuration_id: o": flag_bucket
            and flag_event_name
            and flag_configuration_id,
            "bucket: x, key: o, event_name: o, configuration_id: o": flag_key
            and flag_event_name
            and flag_configuration_id,
            "bucket: o, key: o, event_name: x, configuration_id: x": flag_bucket and flag_key,
            "bucket: o, key: x, event_name: o, configuration_id: x": flag_bucket and flag_event_name,
            "bucket: x, key: o, event_name: o, configuration_id: x": flag_key and flag_event_name,
            "bucket: o, key: x, event_name: x, configuration_id: o": flag_bucket and flag_configuration_id,
            "bucket: x, key: o, event_name: x, configuration_id: o": flag_key and flag_configuration_id,
            "bucket: x, key: x, event_name: o, configuration_id: o": flag_event_name and flag_configuration_id,
            "bucket: o, key: x, event_name: x, configuration_id: x": flag_bucket,
            "bucket: x, key: o, event_name: x, configuration_id: x": flag_key,
            "bucket: x, key: x, event_name: o, configuration_id: x": flag_event_name,
            "bucket: x, key: x, event_name: x, configuration_id: o": flag_configuration_id,
            "bucket: x, key: x, event_name: x, configuration_id: x": False,
        }

        return mapping[text]

    def match(self, event: dict[str, Any]) -> tuple[Callable, S3Event] | None:
        if not isinstance(event, dict):
            return None

        all_records: list[dict[str, Any]] = event.get("Records", [])

        if len(all_records) == 0:
            return None

        record = all_records[0]
        event_name = record.get("eventName")
        s3_data = record.get("s3")
        if not event_name or not s3_data:
            return None

        bucket: str | None = s3_data.get("bucket", {}).get("name")
        key: str | None = s3_data.get("object", {}).get("key")
        configuration_id: str | None = s3_data.get("configurationId")

        if not bucket and not key and not configuration_id:
            return None

        if not self.bucket and not self.bucket_prefix:
            bucket = None

        if not self.key and not self.key_prefix and not self.key_suffix:
            key = None

        if not self.event_name and not self.event_name_prefix:
            event_name = None

        if not self.configuration_id and not self.configuration_id_prefix:
            configuration_id = None

        if self.is_target(bucket, key, event_name, configuration_id):
            return self.func, S3Event(event)
        else:
            return None
