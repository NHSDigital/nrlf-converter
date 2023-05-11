from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from nrlf_converter.nrl.constants import (
    CUSTODIAN_ODS_REGEX,
    DEFAULT_SYSTEM,
    RELATES_TO_REPLACES_REGEX,
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


@dataclass
class Coding(ValidatedModel):
    code: str = validate_against_schema(schema=str)
    display: str = validate_against_schema(schema=str)
    id: Optional[str] = validate_against_schema(schema=str, optional=True)
    system: Optional[str] = validate_against_schema(
        schema=str, optional=True, default=DEFAULT_SYSTEM
    )


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


@dataclass
class Reference(ValidatedModel):
    reference: Optional[str] = validate_against_schema(schema=str, optional=True)
    identifier: Optional[Identifier] = validate_against_schema(
        schema=Identifier, optional=True
    )


@dataclass
class DataDocumentType(ValidatedModel):
    code: str = validate_against_schema(schema=str)
    display: str = validate_against_schema(schema=str)


@dataclass
class RelatesTo(ValidatedModel):
    code: Optional[str] = validate_against_schema(schema=str, optional=True)
    target: Reference = validate_against_schema(schema=Reference)

    @property
    def logical_id(self):
        if self.code != REPLACES:
            return None

        if self.target.reference is None:
            raise BadRelatesTo(
                f"DocumentPointer 'relatesTo.code' equals '{REPLACES}' but "
                "no value was provided for 'relatesTo.target.reference'"
            )
        result: re.Match = RELATES_TO_REPLACES_REGEX.match(self.target.reference)
        if result is None:
            raise BadRelatesTo(
                f"Could not parse an logicalId from '{self.target.reference}'"
                f" using pattern '{RELATES_TO_REPLACES_REGEX.pattern}'"
            )
        return result.groupdict()["logical_id"]


@dataclass
class DocumentPointer(ValidatedModel):
    status: Literal["current"] = validate_literal(value="current")
    type: Coding = validate_against_schema(schema=Coding)
    class_: CodeableConcept = validate_against_schema(schema=CodeableConcept)
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
    # Not used in transformation to DocumentReference
    masterIdentifier: Optional[Identifier] = validate_against_schema(
        schema=Identifier, optional=True
    )
    created: Optional[datetime] = validate_datetime(optional=True)
    attachment: Attachment = validate_against_schema(schema=Attachment)
    format: Coding = validate_against_schema(schema=Coding)
    meta: Metadata = validate_against_schema(schema=Metadata)
    stability: CodeableConcept = validate_against_schema(schema=CodeableConcept)
    removed: Literal[False] = validate_literal(value=False)

    @property
    def ods_code(self):
        result: re.Match = CUSTODIAN_ODS_REGEX.match(self.custodian.reference)
        if result is None:
            raise CustodianError(
                f"Could not parse an ODS code from '{self.custodian.reference}'"
                f" using pattern '{CUSTODIAN_ODS_REGEX.pattern}'"
            )
        return result.groupdict()["ods_code"]
