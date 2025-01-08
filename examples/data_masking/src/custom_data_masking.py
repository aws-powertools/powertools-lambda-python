from __future__ import annotations

from aws_lambda_powertools.utilities.data_masking import DataMasking
from aws_lambda_powertools.utilities.typing import LambdaContext

data_masker = DataMasking()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    data: dict = event.get("body", {})

    # Default erase (*****)
    default_erased = data_masker.erase(data, fields=["address.zip"])
    # 'street': '*****'

    # dynamic_mask
    dynamic_mask = data_masker.erase(data, fields=["address.zip"], dynamic_mask=True)
    #'street': '*** **** **'

    # custom_mask
    custom_mask = data_masker.erase(data, fields=["address.zip"], custom_mask="XX")
    #'zip': 'XX'

    # regex_pattern and mask_format
    regex_pattern = data_masker.erase(data, fields=["email"], regex_pattern=r"(.)(.*)(@.*)", mask_format=r"\1****\3")
    #'email': 'j****@example.com'

    # Masking rules for each field
    masking_rules = {
        "email": {"regex_pattern": "(.)(.*)(@.*)", "mask_format": r"\1****\3"},
        "age": {"dynamic_mask": True},
        "address.zip": {"dynamic_mask": True, "custom_mask": "xxx"},
        "address.street": {"dynamic_mask": False},
    }

    masking_rules_erase = data_masker.erase(data, masking_rules=masking_rules)

    return default_erased, dynamic_mask, custom_mask, regex_pattern, masking_rules_erase
