import importlib
from types import ModuleType

import pytest

from aws_lambda_powertools.utilities._data_masking.base import DataMasking

DATA_MASKING_PACKAGE = "aws_lambda_powertools.utilities._data_masking"
DATA_MASKING_INIT_SLA: float = 0.002
DATA_MASKING_NESTED_ENCRYPT_SLA: float = 0.05

json_blob = {
    "id": 1,
    "name": "John Doe",
    "age": 30,
    "email": "johndoe@example.com",
    "address": {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
    "phone_numbers": ["+1-555-555-1234", "+1-555-555-5678"],
    "interests": ["Hiking", "Traveling", "Photography", "Reading"],
    "job_history": {
        "company": {
            "company_name": "Acme Inc.",
            "company_address": "5678 Interview Dr.",
        },
        "position": "Software Engineer",
        "start_date": "2015-01-01",
        "end_date": "2017-12-31",
    },
    "about_me": """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt velit quis
    sapien mollis, at egestas massa tincidunt. Suspendisse ultrices arcu a dolor dapibus,
    ut pretium turpis volutpat. Vestibulum at sapien quis sapien dignissim volutpat ut a enim.
    Praesent fringilla sem eu dui convallis luctus. Donec ullamcorper, sapien ut convallis congue,
    risus mauris pretium tortor, nec dignissim arcu urna a nisl. Vivamus non fermentum ex. Proin
    interdum nisi id sagittis egestas. Nam sit amet nisi nec quam pharetra sagittis. Aliquam erat
    volutpat. Donec nec luctus sem, nec ornare lorem. Vivamus vitae orci quis enim faucibus placerat.
    Nulla facilisi. Proin in turpis orci. Donec imperdiet velit ac tellus gravida, eget laoreet tellus
    malesuada. Praesent venenatis tellus ac urna blandit, at varius felis posuere. Integer a commodo nunc.
    """,
}
json_blob_fields = ["address.street", "job_history.company.company_name"]


def import_data_masking_utility() -> ModuleType:
    """Dynamically imports and return DataMasking module"""
    return importlib.import_module(DATA_MASKING_PACKAGE)


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_data_masking_init(benchmark):
    benchmark.pedantic(import_data_masking_utility)
    stat = benchmark.stats.stats.max
    if stat > DATA_MASKING_INIT_SLA:
        pytest.fail(f"High level imports should be below {DATA_MASKING_INIT_SLA}s: {stat}")


def mask_json_blob():
    data_masker = DataMasking()
    data_masker.mask(json_blob, json_blob_fields)


@pytest.mark.perf
@pytest.mark.benchmark(group="core", disable_gc=True, warmup=False)
def test_data_masking_encrypt_with_json_blob(benchmark):
    benchmark.pedantic(mask_json_blob)
    stat = benchmark.stats.stats.max
    if stat > DATA_MASKING_NESTED_ENCRYPT_SLA:
        pytest.fail(f"High level imports should be below {DATA_MASKING_NESTED_ENCRYPT_SLA}s: {stat}")
