import json

import pytest

from nrlf_converter.utils.constants import EMPTY_VALUES
from nrlf_converter.utils.utils import strip_empty_json_paths

NULLISH_VALUES = ["null", "[]", "{}", '""']


def test_nullish_fields_consistent_with_empty_values():
    assert sorted(NULLISH_VALUES) == sorted(map(json.dumps, EMPTY_VALUES))


@pytest.mark.parametrize(
    "bad_json",
    (
        {"foo": {"bar": [None]}, "oof": "rab"},
        {"foo": {"bar": []}, "oof": "rab"},
        {"foo": {}, "oof": "rab"},
    ),
)
def test_strip_empty_json_paths(bad_json):
    # Confirm bad fields are present
    bad_json_str = json.dumps(bad_json)
    assert any(nullish_field in bad_json_str for nullish_field in NULLISH_VALUES)

    stripped_bad_json = strip_empty_json_paths(bad_json)
    assert stripped_bad_json == {"oof": "rab"}

    # Confirm bad fields are gone
    stripped_bad_json_str = json.dumps(stripped_bad_json)
    assert not any(
        nullish_field in stripped_bad_json_str for nullish_field in NULLISH_VALUES
    )
