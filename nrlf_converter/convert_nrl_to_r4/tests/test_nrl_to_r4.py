import json
from dataclasses import asdict
from datetime import datetime
from unittest import mock

import hypothesis
import pytest
from hypothesis.strategies import dictionaries, integers, just, lists, text
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from nrlf_converter.convert_nrl_to_r4.nrl_to_r4 import (
    _nrlf_id,
    _relates_to,
    nrl_to_r4,
    reject_empty_args,
)
from nrlf_converter.nrl.document_pointer import DocumentPointer
from nrlf_converter.nrl.tests.test_document_pointer import valid_document_pointer
from nrlf_converter.r4.document_reference import DocumentReference as _DocumentReference
from nrlf_converter.utils.constants import EMPTY_VALUES
from nrlf_converter.utils.utils import strip_empty_json_paths
from nrlf_converter.utils.validation.errors import ValidationError


@dataclass(config=ConfigDict(extra="forbid"))
class PydanticDocumentReference(_DocumentReference):
    pass


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


@hypothesis.given(document_pointer=valid_document_pointer)
def test__nrl_to_r4(document_pointer: DocumentPointer):
    _document_pointer = asdict(document_pointer)
    _document_pointer["class"] = _document_pointer.pop("class_")
    document_reference_json = nrl_to_r4(
        document_pointer=_document_pointer, nhs_number="3964056618", asid="230811201350"
    )
    document_reference = PydanticDocumentReference(**document_reference_json)
    _document_reference_str = json.dumps(document_reference.dict(), default=json_serial)
    _document_reference = json.loads(_document_reference_str)
    assert _document_reference == document_reference_json


@hypothesis.given(ods_code=text(min_size=1), logical_id=text(min_size=1))
def test__nrlf_id(ods_code: str, logical_id: str):
    assert (
        _nrlf_id(ods_code=ods_code, logical_id=logical_id) == f"{ods_code}-{logical_id}"
    )


def test__relates_to():
    relatesTo = mock.MagicMock()
    relatesTo.logical_id = "LOGICAL_ID"
    relatesTo.code = "CODE"

    relates_to = _relates_to(relatesTo=relatesTo, ods_code="ODS_CODE")
    assert strip_empty_json_paths(asdict(relates_to)) == {
        "code": "CODE",
        "target": {"identifier": {"value": "ODS_CODE-LOGICAL_ID"}},
    }


@reject_empty_args
def my_func(a, b, c, d):
    return f"{a}, {b}, {c}, {d}"


@hypothesis.given(
    a=integers(),
    b=text(min_size=1),
    c=lists(integers(), min_size=1),
    d=dictionaries(keys=integers(), values=just("value"), min_size=1),
)
def test_reject_empty_args(a, b, c, d):
    assert my_func(a, b, c, d) == f"{a}, {b}, {c}, {d}"


@pytest.mark.parametrize("a", EMPTY_VALUES)
@hypothesis.given(
    b=text(min_size=1),
    c=lists(integers(), min_size=1),
    d=dictionaries(keys=integers(), values=just("value"), min_size=1),
)
def test_reject_empty_args_fail(a, b, c, d):
    with pytest.raises(ValidationError):
        my_func(a, b, c, d)
