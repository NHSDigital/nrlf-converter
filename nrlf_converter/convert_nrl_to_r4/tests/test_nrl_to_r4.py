import json
from dataclasses import asdict
from datetime import datetime
from typing import List
from unittest import mock

import hypothesis
import pytest
from hypothesis.strategies import (
    dictionaries,
    integers,
    just,
    lists,
    sampled_from,
    text,
)
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from nrlf_converter.convert_nrl_to_r4.nrl_to_r4 import (
    _content_items,
    _https_to_ssp,
    _nrlf_id,
    _relates_to,
    nrl_to_r4,
    reject_empty_args,
)
from nrlf_converter.nrl.constants import CUSTODIAN_ODS_REGEX
from nrlf_converter.nrl.document_pointer import ContentItem as ContentItem
from nrlf_converter.nrl.document_pointer import DocumentPointer
from nrlf_converter.nrl.tests.test_document_pointer import (
    non_ssp_content_items,
    ssp_content_items,
    valid_document_pointer,
)
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


@hypothesis.given(
    document_pointer=valid_document_pointer,
    asid=sampled_from(["230811201350", *EMPTY_VALUES]),
)
def test__nrl_to_r4(document_pointer: DocumentPointer, asid: str):
    _document_pointer = asdict(document_pointer)
    _document_pointer["class"] = _document_pointer.pop("class_")
    document_reference_json = nrl_to_r4(
        document_pointer=_document_pointer, nhs_number="3964056618", asid=asid
    )
    document_reference = PydanticDocumentReference(**document_reference_json)
    _document_reference_str = json.dumps(document_reference.dict(), default=json_serial)
    _document_reference = json.loads(_document_reference_str)
    assert _document_reference == document_reference_json


@hypothesis.given(
    document_pointer=valid_document_pointer,
    asid=just("230811201350"),
    ssp_content_items=ssp_content_items,
)
def test__nrl_to_r4_ssp_type(
    document_pointer: DocumentPointer, asid: str, ssp_content_items: List[ContentItem]
):
    document_pointer.content = ssp_content_items
    _document_pointer = asdict(document_pointer)
    _document_pointer["class"] = _document_pointer.pop("class_")
    document_reference_json = nrl_to_r4(
        document_pointer=_document_pointer, nhs_number="3964056618", asid=asid
    )
    document_reference = PydanticDocumentReference(**document_reference_json)
    _document_reference_str = json.dumps(document_reference.dict(), default=json_serial)
    _document_reference = json.loads(_document_reference_str)
    assert _document_reference == document_reference_json


@hypothesis.given(document_pointer=valid_document_pointer, asid=just("230811201350"))
def test__nrl_to_r4_author_reference(document_pointer: DocumentPointer, asid: str):
    _document_pointer = asdict(document_pointer)
    _document_pointer["class"] = _document_pointer.pop("class_")
    document_reference_json = nrl_to_r4(
        document_pointer=_document_pointer, nhs_number="3964056618", asid=asid
    )
    expected_author = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "230811201350",
            }
        },
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": CUSTODIAN_ODS_REGEX.match(
                    document_pointer.author.reference
                ).groupdict()["ods_code"],
            }
        },
    ]
    assert document_reference_json["author"] == expected_author


@hypothesis.given(
    document_pointer=valid_document_pointer,
    asid=sampled_from(EMPTY_VALUES),
    ssp_content_items=ssp_content_items,
)
def test__nrl_to_r4__ssp_type_but_no_asid(
    document_pointer: DocumentPointer, asid: str, ssp_content_items: List[ContentItem]
):
    document_pointer.content = ssp_content_items
    _document_pointer = asdict(document_pointer)
    _document_pointer["class"] = _document_pointer.pop("class_")

    with pytest.raises(ValidationError):
        nrl_to_r4(
            document_pointer=_document_pointer, nhs_number="3964056618", asid=asid
        )


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


@reject_empty_args()
def my_func(a, b, c, d):
    return f"{a}, {b}, {c}, {d}"


@reject_empty_args(exemptions=["d"])
def my_other_func(a, b, c, d):
    return f"{a}, {b}, {c}, {d}"


@hypothesis.given(
    a=integers(),
    b=text(min_size=1),
    c=lists(integers(), min_size=1),
    d=dictionaries(keys=integers(), values=just("value"), min_size=1),
)
def test_reject_empty_args(a, b, c, d):
    assert my_func(a, b=b, c=c, d=d) == f"{a}, {b}, {c}, {d}"


@pytest.mark.parametrize("a", EMPTY_VALUES)
@hypothesis.given(
    b=text(min_size=1),
    c=lists(integers(), min_size=1),
    d=dictionaries(keys=integers(), values=just("value"), min_size=1),
)
def test_reject_empty_args_fail(a, b, c, d):
    with pytest.raises(ValidationError):
        my_func(a=a, b=b, c=c, d=d)


@hypothesis.given(a=integers(), b=text(min_size=1), c=lists(integers(), min_size=1))
@pytest.mark.parametrize("d", EMPTY_VALUES)
def test_reject_empty_args_with_exemptions(a, b, c, d):
    assert my_other_func(a, b=b, c=c, d=d) == f"{a}, {b}, {c}, {d}"


@pytest.mark.parametrize("a", EMPTY_VALUES)
@hypothesis.given(
    b=text(min_size=1),
    c=lists(integers(), min_size=1),
)
@pytest.mark.parametrize("d", EMPTY_VALUES)
def test_reject_empty_args_fail_with_exemptions(a, b, c, d):
    with pytest.raises(ValidationError):
        my_other_func(a, b=b, c=c, d=d)


@pytest.mark.parametrize(
    "protocol",
    [
        "https://",
    ],
)
@hypothesis.given(url=text(min_size=1))
def test__https_to_ssp(protocol, url):
    assert _https_to_ssp(https_url=protocol + url) == "ssp://" + url


@pytest.mark.parametrize(
    "protocol",
    ["ssp://", "http://", "blah", ""],
)
@hypothesis.given(url=text(min_size=1))
def test__https_to_ssp_failure(protocol, url):
    with pytest.raises(ValidationError):
        assert _https_to_ssp(https_url=protocol + url)


@hypothesis.given(
    non_ssp_content_items=non_ssp_content_items, ssp_content_items=ssp_content_items
)
def test__content_items(
    non_ssp_content_items: List[ContentItem],
    ssp_content_items: List[ContentItem],
):
    content_items = non_ssp_content_items + ssp_content_items
    document_reference_content_items = list(_content_items(content_items=content_items))

    assert len(content_items) == len(document_reference_content_items)

    non_ssp_document_reference_content_items = document_reference_content_items[
        : len(non_ssp_content_items)
    ]
    ssp_document_reference_content_items = document_reference_content_items[
        len(non_ssp_content_items) :
    ]

    assert len(ssp_content_items) == len(ssp_document_reference_content_items)

    for item, _item in zip(
        non_ssp_content_items, non_ssp_document_reference_content_items
    ):
        assert asdict(item.attachment) == asdict(_item.attachment)
        assert asdict(item.format) == asdict(_item.format)

    for item, _item in zip(ssp_content_items, ssp_document_reference_content_items):
        assert asdict(item.format) == asdict(_item.format)
        assert (
            _item.format.system
            == "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode"
        )
        assert asdict(item.attachment) != asdict(_item.attachment)
        item.attachment.url = "ssp://foo.bar"
        assert asdict(item.attachment) == asdict(_item.attachment)
