from __future__ import annotations

from typing import Union

from .constants import EMPTY_VALUES, JSON_TYPES


def strip_empty_json_paths(json: Union[list[dict], dict]) -> Union[list[dict], dict]:
    stripped_json = json
    modified = False
    if type(json) is list:
        stripped_json = []
        for item in json:
            if type(item) in JSON_TYPES:
                item = strip_empty_json_paths(item)
            if item in EMPTY_VALUES:
                modified = True
            else:
                stripped_json.append(item)
    elif type(json) is dict:
        stripped_json = {}
        for key, value in json.items():
            if type(value) in JSON_TYPES:
                value = strip_empty_json_paths(value)
            if value in EMPTY_VALUES:
                modified = True
            else:
                stripped_json[key] = value

    return strip_empty_json_paths(stripped_json) if modified else stripped_json
