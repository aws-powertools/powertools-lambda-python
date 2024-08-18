import re

RULES_KEY = "rules"
FEATURE_DEFAULT_VAL_KEY = "default"
CONDITIONS_KEY = "conditions"
RULE_MATCH_VALUE = "when_match"
CONDITION_KEY = "key"
CONDITION_VALUE = "value"
CONDITION_ACTION = "action"
FEATURE_DEFAULT_VAL_TYPE_KEY = "boolean_type"
TIME_RANGE_FORMAT = "%H:%M"  # hour:min 24 hours clock
TIME_RANGE_PATTERN = re.compile(r"2[0-3]:[0-5]\d|[0-1]\d:[0-5]\d")  # 24 hour clock
HOUR_MIN_SEPARATOR = ":"
