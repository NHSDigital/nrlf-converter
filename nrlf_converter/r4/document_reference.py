from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Literal, Optional

from nrlf_converter.utils.utils import strip_empty_json_paths


@dataclass
class Coding:
    code: str
    system: str
    display: Optional[str] = None
    id: Optional[str] = None
    userSelected: Optional[bool] = None
    version: Optional[str] = None


@dataclass
class CodeableConcept:
    id: Optional[str] = None
    coding: Optional[List[Coding]] = None


@dataclass
class Period:
    start: Optional[datetime]
    end: Optional[datetime]


@dataclass
class Identifier:
    value: str
    system: Optional[str] = None
    use: Optional[str] = None
    type: Optional[CodeableConcept] = None
    period: Optional[Period] = None
    assigner: Optional[dict] = None


@dataclass
class Reference:
    identifier: Optional[Identifier] = None
    reference: Optional[str] = None


@dataclass
class DocumentReferenceRelatesTo:
    code: str
    target: Reference
    id: Optional[str] = None


@dataclass
class Attachment:
    contentType: str
    url: Optional[str] = None
    data: Optional[str] = None
    language: Optional[str] = None
    creation: Optional[str] = None
    hash: Optional[str] = None
    size: Optional[int] = None
    title: Optional[str] = None


@dataclass
class DocumentReferenceContent:
    attachment: Attachment
    format: Coding
    id: Optional[str] = None


@dataclass
class DocumentReferenceContext:
    period: Optional[Period] = None
    practiceSetting: Optional[CodeableConcept] = None
    related: List[Reference] = None


@dataclass
class DocumentReference:
    id: str
    status: str
    type: CodeableConcept
    category: List[CodeableConcept]
    subject: Reference
    date: datetime
    author: List[Reference]
    custodian: Reference
    content: List[DocumentReferenceContent]
    context: DocumentReferenceContext
    # Optionals and default values
    resourceType: Literal["DocumentReference"] = "DocumentReference"
    relatesTo: Optional[List[DocumentReferenceRelatesTo]] = None

    def dict(self) -> dict:
        _dict = asdict(self)
        return strip_empty_json_paths(_dict)
