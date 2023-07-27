import json
from datetime import datetime
from pathlib import Path

import hypothesis
import pytest
from hypothesis.strategies import builds, data, datetimes, just, lists, text

from nrlf_converter import BadRelatesTo, CustodianError, ValidationError
from nrlf_converter.nrl.constants import SSP, UPDATE_DATE_FORMAT
from nrlf_converter.nrl.document_pointer import (
    Attachment,
    CodeableConcept,
    Coding,
    ContentItem,
    Context,
    DocumentPointer,
    Identifier,
    LogicalIdentifier,
    Metadata,
    Period,
    PracticeSetting,
    Reference,
    RelatesTo,
)

PATH_TO_HERE = Path(__file__).parent
PATH_TO_DATA = PATH_TO_HERE / "data"
PATHS_TO_TEST_DATA = list(PATH_TO_DATA.iterdir())

valid_datetimes = datetimes(
    allow_imaginary=False,
    min_value=datetime(year=1000, day=1, month=1),
    max_value=datetime(year=9999, day=1, month=1),
)
iso_dates = valid_datetimes.map(lambda dt: dt.isoformat())
nrl_dates = valid_datetimes.map(lambda dt: dt.strftime(UPDATE_DATE_FORMAT))
non_empty_str = text(min_size=1)
non_empty_coding = builds(
    Coding, code=non_empty_str, system=non_empty_str, display=non_empty_str
)
non_empty_list_of_coding = lists(non_empty_coding, min_size=1)
non_empty_identifier = builds(Identifier, system=non_empty_str, value=non_empty_str)
non_empty_reference = builds(
    Reference, reference=non_empty_str, identifier=non_empty_identifier
)
non_empty_attachment = builds(Attachment, url=non_empty_str, contentType=non_empty_str)
non_empty_codeable_concept = builds(CodeableConcept, coding=non_empty_list_of_coding)
non_empty_relates_to = builds(RelatesTo, code=non_empty_str, target=non_empty_reference)

non_ssp_content_items = lists(
    builds(ContentItem, format=non_empty_coding, attachment=non_empty_attachment),
    min_size=1,
)
ssp_content_items = lists(
    builds(
        ContentItem,
        format=builds(
            Coding, system=just(SSP.SYSTEM), code=just(SSP.CODE), display=non_empty_str
        ),
        attachment=builds(
            Attachment, url=just("https://foo.bar"), contentType=non_empty_str
        ),
    ),
    min_size=1,
)

valid_document_pointer = builds(
    DocumentPointer,
    type=non_empty_coding,
    class_=non_empty_codeable_concept,
    indexed=iso_dates,
    author=non_empty_reference,
    custodian=builds(
        Reference,
        reference=just(
            "https://directory.spineservices.nhs.uk/STU3/Organization/THE_ODS_CODE"
        ),
        identifier=non_empty_identifier,
    ),
    relatesTo=non_empty_relates_to,
    content=non_ssp_content_items,
    context=builds(
        Context,
        period=builds(Period, start=iso_dates, end=iso_dates),
        practiceSetting=builds(
            PracticeSetting, practiceSettingCoding=non_empty_list_of_coding
        ),
    ),
    logicalIdentifier=builds(LogicalIdentifier, logicalId=non_empty_str),
    lastModified=nrl_dates,
    created=iso_dates,
    meta=builds(
        Metadata,
        lastUpdated=nrl_dates,
        versionId=non_empty_str,
        profile=lists(non_empty_str, min_size=1),
    ),
    masterIdentifier=non_empty_identifier,
    attachment=non_empty_attachment,
    format=non_empty_coding,
    stability=non_empty_codeable_concept,
    status=just("current"),
    removed=just(False),
)


def test_that_test_data_exists():
    assert PATHS_TO_TEST_DATA, "no test data found"


@pytest.mark.parametrize("path_to_data", PATHS_TO_TEST_DATA)
def test_document_pointer(path_to_data):
    with open(path_to_data) as f:
        data: dict = json.load(f)
    DocumentPointer.parse_obj(data)


@hypothesis.given(data=data())
def test_validation_error_with_bad_data(data):
    with pytest.raises(ValidationError):
        data.draw(builds(DocumentPointer))


@hypothesis.given(document_pointer=valid_document_pointer)
def test_ods_code(document_pointer: DocumentPointer):
    assert document_pointer.ods_code == "THE_ODS_CODE"


@hypothesis.given(document_pointer=valid_document_pointer)
def test_ods_code_raises_custodian_error(document_pointer: DocumentPointer):
    document_pointer.custodian.reference = "blah"
    with pytest.raises(CustodianError):
        document_pointer.ods_code


@hypothesis.given(
    relates_to=builds(
        RelatesTo,
        code=just("replaces"),
        target=builds(
            Reference,
            reference=just(
                "https://psis-sync.national.ncrs.nhs.uk/DocumentReference/THE_LOGICAL_ID"
            ),
            identifier=just(None),
        ),
    )
)
def test_relates_to_logical_id_from_reference(relates_to: RelatesTo):
    assert relates_to.logical_id == "THE_LOGICAL_ID"


@hypothesis.given(
    relates_to=builds(
        RelatesTo,
        code=just("replaces"),
        target=builds(
            Reference,
            identifier=builds(
                Identifier, value=just("urn:uuid:THE_LOGICAL_ID"), system=just("system")
            ),
            reference=just(None),
        ),
    )
)
def test_relates_to_logical_id_from_identifier(relates_to: RelatesTo):
    assert relates_to.logical_id == "THE_LOGICAL_ID"


@hypothesis.given(
    relates_to=builds(
        RelatesTo,
        code=just("replaces"),
        target=builds(
            Reference,
            identifier=builds(
                Identifier, value=just("urn:uuid:THE_LOGICAL_ID"), system=just("system")
            ),
            reference=just(
                "https://psis-sync.national.ncrs.nhs.uk/DocumentReference/THE_LOGICAL_ID"
            ),
        ),
    )
)
def test_relates_to_logical_id_raises_bad_relates_if_both_reference_and_identifier_present(
    relates_to: RelatesTo,
):
    with pytest.raises(BadRelatesTo):
        relates_to.logical_id


@hypothesis.given(
    relates_to=builds(RelatesTo, code=just("replaces"), target=non_empty_reference)
)
def test_relates_to_logical_id_raises_bad_relates_to_error(relates_to: RelatesTo):
    with pytest.raises(BadRelatesTo):
        relates_to.logical_id


@hypothesis.given(relates_to=non_empty_relates_to)
def test_relates_to_logical_id_returns_none_when_not_replaces(relates_to: RelatesTo):
    assert relates_to.logical_id is None


@hypothesis.given(coding=builds(Coding, system=just(SSP.SYSTEM), code=just(SSP.CODE)))
def coding_is_ssp(coding: Coding):
    assert coding.is_ssp()


@hypothesis.given(coding=builds(Coding, system=text(), code=text()))
def coding_is_not_ssp(coding: Coding):
    assert not coding.is_ssp()
