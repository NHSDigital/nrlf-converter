from functools import wraps
from itertools import chain
from typing import Union

from nrlf_converter.nrl.constants import (
    ASID_SYSTEM_URL,
    NHS_NUMBER_SYSTEM_URL,
    ODS_SYSTEM,
)
from nrlf_converter.nrl.document_pointer import DocumentPointer, RelatesTo
from nrlf_converter.r4.constants import ID_SEPARATOR
from nrlf_converter.r4.document_reference import (
    CodeableConcept,
    DocumentReference,
    DocumentReferenceContent,
    DocumentReferenceContext,
    DocumentReferenceRelatesTo,
    Identifier,
    Reference,
)
from nrlf_converter.utils.constants import EMPTY_VALUES, JSON_TYPES
from nrlf_converter.utils.utils import strip_empty_json_paths
from nrlf_converter.utils.validation.errors import ValidationError


def _nrlf_id(ods_code: str, logical_id: str):
    return f"{ods_code}{ID_SEPARATOR}{logical_id}"


def _relates_to(
    relatesTo: RelatesTo, ods_code: str
) -> Union[RelatesTo, DocumentReferenceRelatesTo]:
    if relatesTo and relatesTo.logical_id:
        return DocumentReferenceRelatesTo(
            code=relatesTo.code,
            target=Reference(
                identifier=Identifier(
                    value=_nrlf_id(ods_code=ods_code, logical_id=relatesTo.logical_id)
                )
            ),
        )
    return relatesTo


def _is_empty(obj):
    if type(obj) in JSON_TYPES:
        obj = strip_empty_json_paths(obj)
    return obj in EMPTY_VALUES


def reject_empty_args(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if any(map(_is_empty, chain(args, kwargs.values()))):
            raise ValidationError(
                message=f"One or more empty or null values passed to {fn.__name__}"
            )

        return fn(*args, **kwargs)

    return wrapper


@reject_empty_args
def nrl_to_r4(document_pointer: dict, nhs_number: str, asid: str) -> dict:
    _document_pointer = DocumentPointer.parse_obj(document_pointer)
    document_reference = DocumentReference(
        id=_nrlf_id(
            ods_code=_document_pointer.ods_code,
            logical_id=_document_pointer.logicalIdentifier.logicalId,
        ),
        status=_document_pointer.status,
        type=CodeableConcept(coding=[_document_pointer.type]),
        category=[_document_pointer.class_],
        subject=Reference(
            identifier=Identifier(system=NHS_NUMBER_SYSTEM_URL, value=nhs_number)
        ),
        date=_document_pointer.indexed,
        author=[
            Reference(identifier=Identifier(system=ASID_SYSTEM_URL, value=asid)),
            _document_pointer.author,
        ],
        custodian=Reference(
            identifier=Identifier(system=ODS_SYSTEM, value=_document_pointer.ods_code)
        ),
        relatesTo=[
            _relates_to(
                relatesTo=_document_pointer.relatesTo,
                ods_code=_document_pointer.ods_code,
            )
        ],
        content=[
            DocumentReferenceContent(
                attachment=content.attachment, format=content.format
            )
            for content in _document_pointer.content
        ],
        context=DocumentReferenceContext(
            period=_document_pointer.context.period,
            practiceSetting=CodeableConcept(
                coding=_document_pointer.context.practiceSetting.practiceSettingCoding
            ),
        ),
    )
    return document_reference.dict()
