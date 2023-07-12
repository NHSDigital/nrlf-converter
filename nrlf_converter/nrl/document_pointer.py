from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from nrlf_converter.nrl.constants import (
    CUSTODIAN_ODS_REGEX,
    DEFAULT_SYSTEM,
    RELATES_TO_REPLACES_IDENTIFIER_REGEXES,
    RELATES_TO_REPLACES_REFERENCE_REGEXES,
    REPLACES,
    UPDATE_DATE_FORMAT,
)
from nrlf_converter.nrl.errors import BadRelatesTo, CustodianError
from nrlf_converter.utils.validation.model import ValidatedModel
from nrlf_converter.utils.validation.validators import (
    validate_against_schema,
    validate_datetime,
    validate_literal,
)


@dataclass
class Attachment(ValidatedModel):
    url: str = validate_against_schema(schema=str)
    contentType: str = validate_against_schema(schema=str)
    data: Optional[str] = validate_against_schema(schema=str, optional=True)
    language: Optional[str] = validate_against_schema(schema=str, optional=True)
    creation: Optional[str] = validate_against_schema(schema=str, optional=True)
    hash: Optional[str] = validate_against_schema(schema=str, optional=True)
    size: Optional[int] = validate_against_schema(schema=int, optional=True)
    title: Optional[str] = validate_against_schema(schema=str, optional=True)


@dataclass
class Coding(ValidatedModel):
    code: str = validate_against_schema(schema=str)
    display: str = validate_against_schema(schema=str)
    id: Optional[str] = validate_against_schema(schema=str, optional=True)
    system: Optional[str] = validate_against_schema(
        schema=str, optional=True, default=DEFAULT_SYSTEM
    )
    userSelected: Optional[bool] = validate_against_schema(schema=bool, optional=True)
    version: Optional[str] = validate_against_schema(schema=str, optional=True)


@dataclass
class Metadata(ValidatedModel):
    versionId: str = validate_against_schema(schema=str)
    profile: list[str] = validate_against_schema(schema=str, is_list=True)
    lastUpdated: datetime = validate_datetime(date_format=UPDATE_DATE_FORMAT)


@dataclass
class Period(ValidatedModel):
    start: Optional[datetime] = validate_datetime(optional=True)
    end: Optional[datetime] = validate_datetime(optional=True)


@dataclass
class PracticeSetting(ValidatedModel):
    practiceSettingCoding: list[Coding] = validate_against_schema(
        schema=Coding, is_list=True
    )
    practiceSettingText: Optional[str] = validate_against_schema(
        schema=str, optional=True
    )


@dataclass
class Context(ValidatedModel):
    period: Optional[Period] = validate_against_schema(schema=Period, optional=True)
    practiceSetting: PracticeSetting = validate_against_schema(schema=PracticeSetting)


@dataclass
class ValueCodeableConcept(ValidatedModel):
    coding: list[Coding] = validate_against_schema(schema=Coding, is_list=True)


@dataclass
class Extension(ValidatedModel):
    valueCodeableConcept: ValueCodeableConcept = validate_against_schema(
        schema=ValueCodeableConcept
    )
    url: str = validate_against_schema(schema=str)


@dataclass
class ContentItem(ValidatedModel):
    attachment: Attachment = validate_against_schema(schema=Attachment)
    format: Coding = validate_against_schema(schema=Coding)
    extension: Optional[list[Extension]] = validate_against_schema(
        schema=Extension, is_list=True, optional=True
    )


@dataclass
class CodeableConcept(ValidatedModel):
    coding: list[Coding] = validate_against_schema(schema=Coding, is_list=True)
    text: Optional[str] = validate_against_schema(schema=str, optional=True)


@dataclass
class LogicalIdentifier(ValidatedModel):
    logicalId: str = validate_against_schema(schema=str)


@dataclass
class Identifier(ValidatedModel):
    system: str = validate_against_schema(schema=str)
    value: str = validate_against_schema(schema=str)

    use: Optional[str] = validate_against_schema(schema=str, optional=True)
    type: Optional[CodeableConcept] = validate_against_schema(
        schema=CodeableConcept, optional=True
    )
    period: Optional[Period] = validate_against_schema(schema=Period, optional=True)
    assigner: Optional[Reference] = validate_against_schema(schema=dict, optional=True)


@dataclass
class Reference(ValidatedModel):
    reference: Optional[str] = validate_against_schema(schema=str, optional=True)
    identifier: Optional[Identifier] = validate_against_schema(
        schema=Identifier, optional=True
    )
    display: Optional[str] = validate_against_schema(schema=str, optional=True)


def _get_relates_to_target(value: str, regexes: list[re.Pattern]):
    result: re.Match = None
    for regex in regexes:
        result = regex.match(value)
        if result is not None:
            break
    return result


@dataclass
class RelatesTo(ValidatedModel):
    code: Optional[str] = validate_against_schema(schema=str, optional=True)
    target: Reference = validate_against_schema(schema=Reference)

    @property
    def logical_id(self):
        if self.code != REPLACES:
            return None

        has_reference = self.target.reference is not None
        has_identifier = (
            self.target.identifier and self.target.identifier.value is not None
        )

        result: re.Match = None
        if has_reference and has_identifier:
            raise BadRelatesTo(
                f"DocumentPointer 'relatesTo.code' equals '{REPLACES}' but "
                "a value was provided for both 'relatesTo.target.reference' and "
                "'relatesTo.target.identifier.value', so the relatesTo is ambiguous."
            )
        elif has_reference:
            result = _get_relates_to_target(
                value=self.target.reference,
                regexes=RELATES_TO_REPLACES_REFERENCE_REGEXES,
            )
        elif has_identifier:
            result = _get_relates_to_target(
                value=self.target.identifier.value,
                regexes=RELATES_TO_REPLACES_IDENTIFIER_REGEXES,
            )
        else:
            raise BadRelatesTo(
                f"DocumentPointer 'relatesTo.code' equals '{REPLACES}' but "
                "no value was provided for either 'relatesTo.target.reference' "
                "or 'relatesTo.target.identifier.value'"
            )

        if result is None:
            raise BadRelatesTo(
                f"Could not parse an logicalId from '{reference}'"
                f" using patterns '{(regex.pattern for regex in RELATES_TO_REPLACES_REFERENCE_REGEXES)}'"
            )

        return result.groupdict()["logical_id"]


@dataclass
class DocumentPointer(ValidatedModel):
    status: Literal["current"] = validate_literal(value="current")
    type: Coding = validate_against_schema(schema=Coding)
    class_: Optional[CodeableConcept] = validate_against_schema(
        schema=CodeableConcept, optional=True
    )
    indexed: datetime = validate_datetime()
    author: Reference = validate_against_schema(schema=Reference)
    custodian: Reference = validate_against_schema(schema=Reference)
    relatesTo: Optional[RelatesTo] = validate_against_schema(
        schema=RelatesTo, optional=True
    )
    content: list[ContentItem] = validate_against_schema(
        schema=ContentItem, is_list=True
    )
    context: Context = validate_against_schema(schema=Context)
    logicalIdentifier: LogicalIdentifier = validate_against_schema(
        schema=LogicalIdentifier
    )
    # Used to update DocumentPointer.[dates]
    lastModified: datetime = validate_datetime(date_format=UPDATE_DATE_FORMAT)
    # None of the following are used in transformation to DocumentReference
    # so loose validation is applied (i.e. str, dict instead of more complex objects)
    masterIdentifier: Optional[Identifier] = validate_against_schema(
        schema=dict, optional=True
    )
    created: Optional[datetime] = validate_against_schema(schema=str, optional=True)
    attachment: Optional[Attachment] = validate_against_schema(
        schema=dict, optional=True
    )
    format: Optional[Coding] = validate_against_schema(schema=dict, optional=True)
    meta: Optional[Metadata] = validate_against_schema(schema=dict, optional=True)
    stability: Optional[CodeableConcept] = validate_against_schema(
        schema=dict, optional=True
    )
    removed: Optional[bool] = validate_against_schema(schema=bool, optional=True)

    @property
    def ods_code(self):
        result: re.Match = CUSTODIAN_ODS_REGEX.match(self.custodian.reference)
        if result is None:
            raise CustodianError(
                f"Could not parse an ODS code from '{self.custodian.reference}'"
                f" using pattern '{CUSTODIAN_ODS_REGEX.pattern}'"
            )
        return result.groupdict()["ods_code"]
