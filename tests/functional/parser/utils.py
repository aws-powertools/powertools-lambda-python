import json
import os


def get_event_file_path(file_name: str) -> dict:
    return os.path.dirname(os.path.realpath(__file__)) + "/../../events/" + file_name


def load_event(file_name: str) -> dict:
    full_file_name = os.path.dirname(os.path.realpath(__file__)) + "/../../events/" + file_name
    with open(full_file_name) as fp:
        return json.load(fp)
