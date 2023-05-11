from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pytest

from nrlf_converter.utils.validation.errors import ValidationError
from nrlf_converter.utils.validation.model import ValidatedModel
from nrlf_converter.utils.validation.validators import (
    validate_against_schema,
    validate_datetime,
    validate_literal,
)


@dataclass
class Property(ValidatedModel):
    str_value: str = validate_against_schema(schema=str)
    list_int_value: list[int] = validate_against_schema(schema=int, is_list=True)
    iso_datetime_value: datetime = validate_datetime()
    non_iso_datetime_value: datetime = validate_datetime(date_format="%Y:%m:%d")
    literal_value: Literal["the_literal_value"] = validate_literal(
        value="the_literal_value"
    )


@dataclass
class Item(ValidatedModel):
    property: Property = validate_against_schema(schema=Property)


@dataclass
class Container(ValidatedModel):
    items: list[Item] = validate_against_schema(schema=Item, is_list=True)
    item: Item = validate_against_schema(schema=Item)


A_STR = "i am a string"
A_LIST_OF_INT = [123, 456]
A_LIST_OF_MIXED = [123, "not an int"]
AN_ISO_DATETIME = "2022-08-23T14:45:17+00:00"
A_NON_ISO_DATETIME = "2022:12:31"
LITERAL_VALUE = "the_literal_value"

ONLY_PASS_CASE = (
    A_STR,
    A_LIST_OF_INT,
    AN_ISO_DATETIME,
    A_NON_ISO_DATETIME,
    LITERAL_VALUE,
)


@pytest.mark.parametrize("str_value", [A_STR, A_LIST_OF_INT, A_LIST_OF_MIXED])
@pytest.mark.parametrize("list_int_value", [A_LIST_OF_INT, A_LIST_OF_MIXED, A_STR])
@pytest.mark.parametrize(
    "iso_datetime_value", [AN_ISO_DATETIME, A_NON_ISO_DATETIME, A_STR]
)
@pytest.mark.parametrize(
    "non_iso_datetime_value", [A_NON_ISO_DATETIME, AN_ISO_DATETIME, A_STR]
)
@pytest.mark.parametrize("literal_value", [LITERAL_VALUE, A_STR])
def test_validated_model(
    str_value, list_int_value, iso_datetime_value, non_iso_datetime_value, literal_value
):
    container = {
        "item": {
            "property": {
                "str_value": str_value,
                "list_int_value": list_int_value,
                "iso_datetime_value": iso_datetime_value,
                "non_iso_datetime_value": non_iso_datetime_value,
                "literal_value": literal_value,
            }
        },
        "items": [
            {
                "property": {
                    "str_value": str_value,
                    "list_int_value": list_int_value,
                    "iso_datetime_value": iso_datetime_value,
                    "non_iso_datetime_value": non_iso_datetime_value,
                    "literal_value": literal_value,
                }
            }
        ],
    }

    expectation = pytest.raises(ValidationError)
    if (
        str_value,
        list_int_value,
        iso_datetime_value,
        non_iso_datetime_value,
        literal_value,
    ) == ONLY_PASS_CASE:
        expectation = does_not_raise()

    with expectation:
        Container(**container)
