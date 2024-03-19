from dataclasses import asdict
from functools import wraps
from itertools import chain
from typing import Generator, List, Union

from nrlf_converter.nrl.constants import (
    ASID_SYSTEM_URL,
    HTTPS_TO_SSP,
    NHS_NUMBER_SYSTEM_URL,
    ODS_SYSTEM,
)
from nrlf_converter.nrl.document_pointer import (
    Coding,
    ContentItem,
    DocumentPointer,
    RelatesTo,
)
from nrlf_converter.r4.constants import ID_SEPARATOR
from nrlf_converter.r4.document_reference import (
    Attachment,
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


def _https_to_ssp(https_url: str):
    ssp_url = HTTPS_TO_SSP(string=https_url)
    if ssp_url == https_url:
        raise ValidationError(
            f"Failed substitution of 'https://' to 'ssp://' in URL '{https_url}'"
        )
    return ssp_url


def _content_items(
    content_items: List[ContentItem],
) -> Generator[DocumentReferenceContent, None, None]:
    for content in content_items:
        attachment = asdict(content.attachment)
        format = Coding(
            code=content.format.code,
            display=content.format.display,
            system="https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
        )
        if content.format.is_ssp():
            attachment["url"] = _https_to_ssp(content.attachment.url)

        yield DocumentReferenceContent(
            attachment=Attachment(**attachment), format=format
        )


def _is_empty(obj):
    if type(obj) in JSON_TYPES:
        obj = strip_empty_json_paths(obj)
    return obj in EMPTY_VALUES


def reject_empty_args(exemptions: list = None):
    if not exemptions:
        exemptions = []

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            all_args = chain(
                args, (v for k, v in kwargs.items() if k not in exemptions)
            )
            if any(map(_is_empty, all_args)):
                raise ValidationError(
                    message=f"One or more empty or null values passed to {fn.__name__}"
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


@reject_empty_args(exemptions=("asid",))
def nrl_to_r4(document_pointer: dict, nhs_number: str, asid: str = None) -> dict:
    _document_pointer = DocumentPointer.parse_obj(document_pointer)
    if _document_pointer.is_ssp() and not asid:
        raise ValidationError(
            message="ASID must be provided for DocumentPointers with SSP content"
        )
    asid_author: list[Reference] = (
        [Reference(identifier=Identifier(system=ASID_SYSTEM_URL, value=asid))]
        if asid
        else []
    )

    pointer_author: list[Reference] = [
        Reference(
            identifier=Identifier(
                system=ODS_SYSTEM, value=_document_pointer.author_ods_code
            )
        )
    ]

    document_reference = DocumentReference(
        id=_nrlf_id(
            ods_code=_document_pointer.ods_code,
            logical_id=_document_pointer.logicalIdentifier.logicalId,
        ),
        status=_document_pointer.status,
        type=CodeableConcept(coding=[_document_pointer.type]),
        category=[_document_pointer.class_] if _document_pointer.class_ else None,
        subject=Reference(
            identifier=Identifier(system=NHS_NUMBER_SYSTEM_URL, value=nhs_number)
        ),
        date=_document_pointer.indexed,
        author=(asid_author + pointer_author),
        custodian=Reference(
            identifier=Identifier(system=ODS_SYSTEM, value=_document_pointer.ods_code)
        ),
        relatesTo=[
            _relates_to(
                relatesTo=_document_pointer.relatesTo,
                ods_code=_document_pointer.ods_code,
            )
        ],
        content=(
            list(_content_items(content_items=_document_pointer.content))
            if _document_pointer.content
            else []
        ),
        context=(
            DocumentReferenceContext(
                period=_document_pointer.context.period,
                practiceSetting=CodeableConcept(
                    coding=_document_pointer.context.practiceSetting.practiceSettingCoding
                ),
            )
            if _document_pointer.context
            else None
        ),
    )
    return document_reference.dict()
