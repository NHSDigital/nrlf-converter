from dataclasses import Field
from dataclasses import field as dataclasses_field
from dataclasses import fields
from datetime import datetime as dt
from functools import partial
from typing import Type, TypeVar

from .errors import (
    FieldNotFound,
    InconsistentOptionalField,
    InvalidValue,
    TypeMismatch,
    UnexpectedField,
)
from .model import DEFAULT_NOT_SET, ValidationMetadata

SchemaType = TypeVar("SchemaType")
ObjType = TypeVar("ObjType")


def field_validator(obj, optional=False, default=DEFAULT_NOT_SET, **kwargs) -> Field:
    metadata = ValidationMetadata(
        validator=partial(obj, **kwargs), optional=optional, default=default
    )
    return dataclasses_field(
        metadata={ValidationMetadata: metadata},
        default=None if default is DEFAULT_NOT_SET else default,
    )


def validate_against_schema(
    schema: Type[SchemaType],
    is_list=False,
    optional=False,
    default=DEFAULT_NOT_SET,
) -> Field:
    return field_validator(
        _validate_against_schema,
        schema=schema,
        is_list=is_list,
        optional=optional,
        default=default,
    )


def _is_optional(annotation):
    return "Optional[" in str(annotation)


def _validate_against_schema(
    obj: ObjType, schema: Type[SchemaType], is_list=False
) -> SchemaType:
    _schema = None
    if is_list:
        _schema = schema
        schema = list

    if type(obj) is dict:
        schema_fields = fields(schema)
        for field in schema_fields:
            value = obj.get(field.name)
            metadata = ValidationMetadata.from_field(field)
            if (value == metadata.default or value is None) and not metadata.optional:
                raise FieldNotFound(
                    f"Field '{schema.__name__}.{field.name}' was expected but not provided."
                )
            if _is_optional(field.type) is not metadata.optional:
                if metadata.optional:
                    message = "has optional=True but does not use typing.Optional."
                else:
                    message = "uses typing.Optional but has not set optional to True in validate_against_schema."
                raise InconsistentOptionalField(
                    f"Field '{schema.__name__}.{field.name}' {message}"
                )
        for field_name in obj.keys():
            if field_name not in (field.name for field in schema_fields):
                raise UnexpectedField(
                    f"Unexpected field provided: '{schema.__name__}.{field_name}'"
                )
        obj = schema(**obj)

    if type(obj) is not schema:
        raise TypeMismatch(
            f"Item '{obj}' (type '{type(obj).__name__}') was expected to be of type '{schema.__name__}'"
        )

    if is_list:
        obj = [_validate_against_schema(obj=item, schema=_schema) for item in obj]
    return obj


def validate_literal(value, optional=False) -> Field:
    return field_validator(_validate_literal, expected_value=value, optional=optional)


def _validate_literal(obj, expected_value):
    if obj != expected_value:
        raise InvalidValue(
            f"Value '{obj}' was provided, but only '{expected_value}' is allowed."
        )
    return obj


def validate_datetime(date_format: str = None, optional=False):
    return field_validator(
        _validate_datetime, date_format=date_format, optional=optional
    )


def _validate_datetime(obj, date_format: str = None):
    try:
        if date_format is None:
            dt.fromisoformat(obj)
        else:
            dt.strptime(obj, date_format)
    except (ValueError, TypeError):
        raise InvalidValue(f"Could not parse datetime from '{obj}'.") from None
    return obj
