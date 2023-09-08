import copy
import json

from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING

python_dict = {
    "a": {
        "1": {"None": "hello", "four": "world"},  # None type key doesn't work
        "b": {"3": {"4": "goodbye", "e": "world"}},  # key "4.5" doesn't work
    },
}


json_dict = json.dumps(python_dict)


dict_fields = ["a.1.None", "a.b.3.4"]


masked_with_fields = {
    "a": {"1": {"None": DATA_MASKING_STRING, "four": "world"}, "b": {"3": {"4": DATA_MASKING_STRING, "e": "world"}}},
}

aws_encrypted_with_fields = {
    "a": {
        "1": {"None": bytes("hello", "utf-8"), "four": "world"},
        "b": {"3": {"4": bytes("goodbye", "utf-8"), "e": "world"}},
    },
}

# 10kb JSON blob for latency testing
json_blob = {
    "id": 1,
    "name": "John Doe",
    "age": 30,
    "email": "johndoe@example.com",
    "address": {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"},
    "phone_numbers": ["+1-555-555-1234", "+1-555-555-5678"],
    "interests": ["Hiking", "Traveling", "Photography", "Reading"],
    "job_history": {
        "company": "Acme Inc.",
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


json_blob_fields = ["address.street", "job_history.company"]
aws_encrypted_json_blob = copy.deepcopy(json_blob)
aws_encrypted_json_blob["address"]["street"] = bytes("123 Main St", "utf-8")
aws_encrypted_json_blob["job_history"]["company"] = bytes("Acme Inc.", "utf-8")

dictionaries = [python_dict, json_dict, json_blob]
fields_to_mask = [dict_fields, dict_fields, json_blob_fields]


data_types_and_masks = [
    # simple data types
    [42, DATA_MASKING_STRING],
    [4.22, DATA_MASKING_STRING],
    [True, DATA_MASKING_STRING],
    [None, DATA_MASKING_STRING],
    ["this is a string", DATA_MASKING_STRING],
    # iterables
    [[1, 2, 3, 4], [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING]],
    [
        ["hello", 1, 2, 3, "world"],
        [DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING, DATA_MASKING_STRING],
    ],
    # dictionaries
    [python_dict, DATA_MASKING_STRING],
    [json_dict, DATA_MASKING_STRING],
]


data_types = [item[0] for item in data_types_and_masks]
