import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from dateutil import tz

from ... import Logger
from .base import BaseValidator
from .exceptions import SchemaValidationError

RULES_KEY = "rules"
FEATURE_DEFAULT_VAL_KEY = "default"
CONDITIONS_KEY = "conditions"
RULE_MATCH_VALUE = "when_match"
CONDITION_KEY = "key"
CONDITION_VALUE = "value"
CONDITION_ACTION = "action"
FEATURE_DEFAULT_VAL_TYPE_KEY = "boolean_type"
TIME_RANGE_FORMAT = "%H:%M"  # hour:min 24 hours clock
TIME_RANGE_RE_PATTERN = re.compile(r"2[0-3]:[0-5]\d|[0-1]\d:[0-5]\d")  # 24 hour clock
HOUR_MIN_SEPARATOR = ":"


class RuleAction(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    KEY_GREATER_THAN_VALUE = "KEY_GREATER_THAN_VALUE"
    KEY_GREATER_THAN_OR_EQUAL_VALUE = "KEY_GREATER_THAN_OR_EQUAL_VALUE"
    KEY_LESS_THAN_VALUE = "KEY_LESS_THAN_VALUE"
    KEY_LESS_THAN_OR_EQUAL_VALUE = "KEY_LESS_THAN_OR_EQUAL_VALUE"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    IN = "IN"
    NOT_IN = "NOT_IN"
    KEY_IN_VALUE = "KEY_IN_VALUE"
    KEY_NOT_IN_VALUE = "KEY_NOT_IN_VALUE"
    VALUE_IN_KEY = "VALUE_IN_KEY"
    VALUE_NOT_IN_KEY = "VALUE_NOT_IN_KEY"
    SCHEDULE_BETWEEN_TIME_RANGE = "SCHEDULE_BETWEEN_TIME_RANGE"  # hour:min 24 hours clock
    SCHEDULE_BETWEEN_DATETIME_RANGE = "SCHEDULE_BETWEEN_DATETIME_RANGE"  # full datetime format, excluding timezone
    SCHEDULE_BETWEEN_DAYS_OF_WEEK = "SCHEDULE_BETWEEN_DAYS_OF_WEEK"  # MONDAY, TUESDAY, .... see TimeValues enum
    MODULO_RANGE = "MODULO_RANGE"


class TimeKeys(Enum):
    """
    Possible keys when using time rules
    """

    CURRENT_TIME = "CURRENT_TIME"
    CURRENT_DAY_OF_WEEK = "CURRENT_DAY_OF_WEEK"
    CURRENT_DATETIME = "CURRENT_DATETIME"


class TimeValues(Enum):
    """
    Possible values when using time rules
    """

    START = "START"
    END = "END"
    TIMEZONE = "TIMEZONE"
    DAYS = "DAYS"
    SUNDAY = "SUNDAY"
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"


class ModuloRangeValues(Enum):
    """
    Possible values when using modulo range rule
    """

    BASE = "BASE"
    START = "START"
    END = "END"


class SchemaValidator(BaseValidator):
    """Validates feature flag schema configuration

    Raises
    ------
    SchemaValidationError
        When schema doesn't conform with feature flag schema

    Schema
    ------

    **Feature object**

    A dictionary containing default value and rules for matching.
    The value MUST be an object and MIGHT contain the following members:

    * **default**: `Union[bool, JSONType]`. Defines default feature value. This MUST be present
    * **boolean_type**: bool. Defines whether feature has non-boolean value (`JSONType`). This MIGHT be present
    * **rules**: `Dict[str, Dict]`. Rules object. This MIGHT be present

    `JSONType` being any JSON primitive value: `Union[str, int, float, bool, None, Dict[str, Any], List[Any]]`

    ```json
    {
        "my_feature": {
            "default": true,
            "rules": {}
        },
        "my_non_boolean_feature": {
            "default": {"group": "read-only"},
            "boolean_type": false,
            "rules": {}
        }
    }
    ```

    **Rules object**

    A dictionary with each rule and their conditions that a feature might have.
    The value MIGHT be present, and when defined it MUST contain the following members:

    * **when_match**: `Union[bool, JSONType]`. Defines value to return when context matches conditions
    * **conditions**: `List[Dict]`. Conditions object. This MUST be present

    ```json
    {
        "my_feature": {
            "default": true,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": false,
                    "conditions": []
                }
            }
        },
        "my_non_boolean_feature": {
            "default": {"group": "read-only"},
            "boolean_type": false,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": {"group": "admin"},
                    "conditions": []
                }
            }
        }
    }
    ```

    **Conditions object**

    A list of dictionaries containing conditions for a given rule.
    The value MUST contain the following members:

    * **action**: `str`. Operation to perform to match a key and value.
    The value MUST be either EQUALS, STARTSWITH, ENDSWITH,
    KEY_IN_VALUE KEY_NOT_IN_VALUE VALUE_IN_KEY VALUE_NOT_IN_KEY

    * **key**: `str`. Key in given context to perform operation
    * **value**: `Any`. Value in given context that should match action operation.

    ```json
    {
        "my_feature": {
            "default": true,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": false,
                    "conditions": [
                        {
                            "action": "EQUALS",
                            "key": "tenant_id",
                            "value": "345345435",
                        }
                    ]
                }
            }
        }
    }
    ```
    """

    def __init__(self, schema: Dict[str, Any], logger: Optional[Union[logging.Logger, Logger]] = None):
        self.schema = schema
        self.logger = logger or logging.getLogger(__name__)

    def validate(self) -> None:
        self.logger.debug("Validating schema")
        if not isinstance(self.schema, dict):
            raise SchemaValidationError(f"Features must be a dictionary, schema={str(self.schema)}")

        features = FeaturesValidator(schema=self.schema, logger=self.logger)
        features.validate()


class FeaturesValidator(BaseValidator):
    """Validates each feature and calls RulesValidator to validate its rules"""

    def __init__(self, schema: Dict, logger: Optional[Union[logging.Logger, Logger]] = None):
        self.schema = schema
        self.logger = logger or logging.getLogger(__name__)

    def validate(self):
        for name, feature in self.schema.items():
            self.logger.debug(f"Attempting to validate feature '{name}'")
            boolean_feature: bool = self.validate_feature(name, feature)
            rules = RulesValidator(feature=feature, boolean_feature=boolean_feature, logger=self.logger)
            rules.validate()

    # returns True in case the feature is a regular feature flag with a  boolean default value
    @staticmethod
    def validate_feature(name, feature) -> bool:
        if not feature or not isinstance(feature, dict):
            raise SchemaValidationError(f"Feature must be a non-empty dictionary, feature={name}")

        default_value: Any = feature.get(FEATURE_DEFAULT_VAL_KEY)
        boolean_feature: bool = feature.get(FEATURE_DEFAULT_VAL_TYPE_KEY, True)
        # if feature is boolean_feature, default_value must be a boolean type.
        # default_value must exist
        # Maintenance: Revisit before going GA. We might to simplify customers on-boarding by not requiring it
        # for non-boolean flags.
        if default_value is None or (not isinstance(default_value, bool) and boolean_feature):
            raise SchemaValidationError(f"feature 'default' boolean key must be present, feature={name}")
        return boolean_feature


class RulesValidator(BaseValidator):
    """Validates each rule and calls ConditionsValidator to validate each rule's conditions"""

    def __init__(
        self,
        feature: Dict[str, Any],
        boolean_feature: bool,
        logger: Optional[Union[logging.Logger, Logger]] = None,
    ):
        self.feature = feature
        self.feature_name = next(iter(self.feature))
        self.rules: Optional[Dict] = self.feature.get(RULES_KEY)
        self.logger = logger or logging.getLogger(__name__)
        self.boolean_feature = boolean_feature

    def validate(self):
        if not self.rules:
            self.logger.debug("Rules are empty, ignoring validation")
            return

        if not isinstance(self.rules, dict):
            self.logger.debug(f"Feature rules must be a dictionary, feature={self.feature_name}")
            raise SchemaValidationError(f"Feature rules must be a dictionary, feature={self.feature_name}")

        for rule_name, rule in self.rules.items():
            self.logger.debug(f"Attempting to validate rule={rule_name} and feature={self.feature_name}")
            self.validate_rule(
                rule=rule,
                rule_name=rule_name,
                feature_name=self.feature_name,
                boolean_feature=self.boolean_feature,
            )
            conditions = ConditionsValidator(rule=rule, rule_name=rule_name, logger=self.logger)
            conditions.validate()

    @staticmethod
    def validate_rule(rule: Dict, rule_name: str, feature_name: str, boolean_feature: bool = True):
        if not rule or not isinstance(rule, dict):
            raise SchemaValidationError(f"Feature rule must be a dictionary, feature={feature_name}")

        RulesValidator.validate_rule_name(rule_name=rule_name, feature_name=feature_name)
        RulesValidator.validate_rule_default_value(rule=rule, rule_name=rule_name, boolean_feature=boolean_feature)

    @staticmethod
    def validate_rule_name(rule_name: str, feature_name: str):
        if not rule_name or not isinstance(rule_name, str):
            raise SchemaValidationError(f"Rule name key must have a non-empty string, feature={feature_name}")

    @staticmethod
    def validate_rule_default_value(rule: Dict, rule_name: str, boolean_feature: bool):
        rule_default_value = rule.get(RULE_MATCH_VALUE)
        if boolean_feature and not isinstance(rule_default_value, bool):
            raise SchemaValidationError(f"'rule_default_value' key must have be bool, rule={rule_name}")


class ConditionsValidator(BaseValidator):
    def __init__(self, rule: Dict[str, Any], rule_name: str, logger: Optional[Union[logging.Logger, Logger]] = None):
        self.conditions: List[Dict[str, Any]] = rule.get(CONDITIONS_KEY, {})
        self.rule_name = rule_name
        self.logger = logger or logging.getLogger(__name__)

    def validate(self):
        if not self.conditions or not isinstance(self.conditions, list):
            self.logger.debug(f"Condition is empty or invalid for rule={self.rule_name}")
            raise SchemaValidationError(f"Invalid condition, rule={self.rule_name}")

        for condition in self.conditions:
            # Condition can contain PII data; do not log condition value
            self.logger.debug(f"Attempting to validate condition for {self.rule_name}")
            self.validate_condition(rule_name=self.rule_name, condition=condition)

    @staticmethod
    def validate_condition(rule_name: str, condition: Dict[str, str]) -> None:
        if not condition or not isinstance(condition, dict):
            raise SchemaValidationError(f"Feature rule condition must be a dictionary, rule={rule_name}")

        ConditionsValidator.validate_condition_action(condition=condition, rule_name=rule_name)
        ConditionsValidator.validate_condition_key(condition=condition, rule_name=rule_name)
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)

    @staticmethod
    def validate_condition_action(condition: Dict[str, Any], rule_name: str):
        action = condition.get(CONDITION_ACTION, "")
        if action not in RuleAction.__members__:
            allowed_values = [_action.value for _action in RuleAction]
            raise SchemaValidationError(
                f"'action' value must be either {allowed_values}, rule_name={rule_name}, action={action}",
            )

    @staticmethod
    def validate_condition_key(condition: Dict[str, Any], rule_name: str):
        key = condition.get(CONDITION_KEY, "")
        if not key or not isinstance(key, str):
            raise SchemaValidationError(f"'key' value must be a non empty string, rule={rule_name}")

        # time actions need to have very specific keys
        # SCHEDULE_BETWEEN_TIME_RANGE => CURRENT_TIME
        # SCHEDULE_BETWEEN_DATETIME_RANGE => CURRENT_DATETIME
        # SCHEDULE_BETWEEN_DAYS_OF_WEEK => CURRENT_DAY_OF_WEEK
        action = condition.get(CONDITION_ACTION, "")
        if action == RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value and key != TimeKeys.CURRENT_TIME.value:
            raise SchemaValidationError(
                f"'condition with a 'SCHEDULE_BETWEEN_TIME_RANGE' action must have a 'CURRENT_TIME' condition key, rule={rule_name}",  # noqa: E501
            )
        if action == RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value and key != TimeKeys.CURRENT_DATETIME.value:
            raise SchemaValidationError(
                f"'condition with a 'SCHEDULE_BETWEEN_DATETIME_RANGE' action must have a 'CURRENT_DATETIME' condition key, rule={rule_name}",  # noqa: E501
            )
        if action == RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value and key != TimeKeys.CURRENT_DAY_OF_WEEK.value:
            raise SchemaValidationError(
                f"'condition with a 'SCHEDULE_BETWEEN_DAYS_OF_WEEK' action must have a 'CURRENT_DAY_OF_WEEK' condition key, rule={rule_name}",  # noqa: E501
            )

    @staticmethod
    def validate_condition_value(condition: Dict[str, Any], rule_name: str):
        value = condition.get(CONDITION_VALUE)
        if value is None:
            raise SchemaValidationError(f"'value' key must not be null, rule={rule_name}")
        action = condition.get(CONDITION_ACTION, "")

        # time actions need to be parsed to make sure date and time format is valid and timezone is recognized
        if action == RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value:
            ConditionsValidator._validate_schedule_between_time_and_datetime_ranges(
                value,
                rule_name,
                action,
                ConditionsValidator._validate_time_value,
            )
        elif action == RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value:
            ConditionsValidator._validate_schedule_between_time_and_datetime_ranges(
                value,
                rule_name,
                action,
                ConditionsValidator._validate_datetime_value,
            )
        elif action == RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value:
            ConditionsValidator._validate_schedule_between_days_of_week(value, rule_name)
        # modulo range condition needs validation on base, start, and end attributes
        elif action == RuleAction.MODULO_RANGE.value:
            ConditionsValidator._validate_modulo_range(value, rule_name)

    @staticmethod
    def _validate_datetime_value(datetime_str: str, rule_name: str):
        date = None

        # We try to parse first with timezone information in order to return the correct error messages
        # when a timestamp with timezone is used. Otherwise, the user would get the first error "must be a valid
        # ISO8601 time format" which is misleading

        try:
            # python < 3.11 don't support the Z timezone on datetime.fromisoformat,
            # so we replace any Z with the equivalent "+00:00"
            # datetime.fromisoformat is orders of magnitude faster than datetime.strptime
            date = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except Exception:
            raise SchemaValidationError(f"'START' and 'END' must be a valid ISO8601 time format, rule={rule_name}")

        # we only allow timezone information to be set via the TIMEZONE field
        # this way we can encode DST into the calculation. For instance, Copenhagen is
        # UTC+2 during winter, and UTC+1 during summer, which would be impossible to define
        # using a single ISO datetime string
        if date.tzinfo is not None:
            raise SchemaValidationError(
                "'START' and 'END' must not include timezone information. Set the timezone using the 'TIMEZONE' "
                f"field, rule={rule_name} ",
            )

    @staticmethod
    def _validate_time_value(time: str, rule_name: str):
        # Using a regex instead of strptime because it's several orders of magnitude faster
        match = TIME_RANGE_RE_PATTERN.match(time)

        if not match:
            raise SchemaValidationError(
                f"'START' and 'END' must be a valid time format, time_format={TIME_RANGE_FORMAT}, rule={rule_name}",
            )

    @staticmethod
    def _validate_schedule_between_days_of_week(value: Any, rule_name: str):
        error_str = f"condition with a CURRENT_DAY_OF_WEEK action must have a condition value dictionary with 'DAYS' and 'TIMEZONE' (optional) keys, rule={rule_name}"  # noqa: E501
        if not isinstance(value, dict):
            raise SchemaValidationError(error_str)

        days = value.get(TimeValues.DAYS.value)
        if not isinstance(days, list) or not value:
            raise SchemaValidationError(error_str)
        for day in days:
            if not isinstance(day, str) or day not in [
                TimeValues.MONDAY.value,
                TimeValues.TUESDAY.value,
                TimeValues.WEDNESDAY.value,
                TimeValues.THURSDAY.value,
                TimeValues.FRIDAY.value,
                TimeValues.SATURDAY.value,
                TimeValues.SUNDAY.value,
            ]:
                raise SchemaValidationError(
                    f"condition value DAYS must represent a day of the week in 'TimeValues' enum, rule={rule_name}",
                )

        timezone = value.get(TimeValues.TIMEZONE.value, "UTC")
        if not isinstance(timezone, str):
            raise SchemaValidationError(error_str)

        # try to see if the timezone string corresponds to any known timezone
        if not tz.gettz(timezone):
            raise SchemaValidationError(f"'TIMEZONE' value must represent a valid IANA timezone, rule={rule_name}")

    @staticmethod
    def _validate_schedule_between_time_and_datetime_ranges(
        value: Any,
        rule_name: str,
        action_name: str,
        validator: Callable[[str, str], None],
    ):
        error_str = f"condition with a '{action_name}' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}"  # noqa: E501
        if not isinstance(value, dict):
            raise SchemaValidationError(error_str)

        start_time = value.get(TimeValues.START.value)
        end_time = value.get(TimeValues.END.value)
        if not start_time or not end_time:
            raise SchemaValidationError(error_str)
        if not isinstance(start_time, str) or not isinstance(end_time, str):
            raise SchemaValidationError(f"'START' and 'END' must be a non empty string, rule={rule_name}")

        validator(start_time, rule_name)
        validator(end_time, rule_name)

        timezone = value.get(TimeValues.TIMEZONE.value, "UTC")
        if not isinstance(timezone, str):
            raise SchemaValidationError(f"'TIMEZONE' must be a string, rule={rule_name}")

        # try to see if the timezone string corresponds to any known timezone
        if not tz.gettz(timezone):
            raise SchemaValidationError(f"'TIMEZONE' value must represent a valid IANA timezone, rule={rule_name}")

    @staticmethod
    def _validate_modulo_range(value: Any, rule_name: str):
        error_str = f"condition with a 'MODULO_RANGE' action must have a condition value type dictionary with 'BASE', 'START' and 'END' keys, rule={rule_name}"  # noqa: E501
        if not isinstance(value, dict):
            raise SchemaValidationError(error_str)

        base = value.get(ModuloRangeValues.BASE.value)
        start = value.get(ModuloRangeValues.START.value)
        end = value.get(ModuloRangeValues.END.value)
        if base is None or start is None or end is None:
            raise SchemaValidationError(error_str)
        if not isinstance(base, int) or not isinstance(start, int) or not isinstance(end, int):
            raise SchemaValidationError(f"'BASE', 'START' and 'END' must be integers, rule={rule_name}")

        if not 0 <= start <= end <= base - 1:
            raise SchemaValidationError(
                f"condition with 'MODULO_RANGE' action must satisfy 0 <= START <= END <= BASE-1, rule={rule_name}",
            )
