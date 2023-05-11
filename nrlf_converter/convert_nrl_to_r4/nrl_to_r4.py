from typing import Union

from nrlf_converter.nrl.constants import NHS_NUMBER_SYSTEM_URL
from nrlf_converter.nrl.document_pointer import ODS_SYSTEM, DocumentPointer, RelatesTo
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


def nrl_to_r4(document_pointer: dict, nhs_number: str) -> dict:
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
        author=[_document_pointer.author],
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
