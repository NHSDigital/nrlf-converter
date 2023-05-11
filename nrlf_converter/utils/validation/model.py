from __future__ import annotations

from dataclasses import Field, dataclass, fields
from types import FunctionType
from typing import Any, Optional, Type, TypeVar

from nrlf_converter.utils.utils import strip_empty_json_paths

from .errors import ValidationError, handle_validation_errors

ModelType = TypeVar("ModelType")


class DefaultNotSet:
    pass


DEFAULT_NOT_SET = DefaultNotSet()


@dataclass
class ValidationMetadata:
    validator: Optional[FunctionType] = None
    optional: Optional[bool] = False
    default: Optional[Any] = DEFAULT_NOT_SET

    @classmethod
    def from_field(cls, field: Field) -> ValidationMetadata:
        return field.metadata.get(ValidationMetadata, DEFAULT_METADATA)


class ValidatedModel:
    def __post_init__(self):
        for field in fields(self):
            value = self.__dict__[field.name]
            metadata = ValidationMetadata.from_field(field)
            if metadata.optional:
                if (value == metadata.default) or (value is None):
                    continue
            if not metadata.validator:
                continue
            with handle_validation_errors(obj=self, field=field.name):
                self.__dict__[field.name] = metadata.validator(value)

    @classmethod
    def parse_obj(cls: Type[ModelType], obj: dict) -> ModelType:
        _stripped_obj = strip_empty_json_paths(obj)
        for field in fields(cls):
            metadata = ValidationMetadata.from_field(field)
            if field.name.endswith("_") and field.name[:-1] in _stripped_obj:
                _stripped_obj[field.name] = _stripped_obj.pop(field.name[:-1], None)
            if field.name not in _stripped_obj and not metadata.optional:
                raise ValidationError(
                    message=f"Field '{cls.__name__}.{field.name}' was expected but not provided."
                )
        return cls(**_stripped_obj)


DEFAULT_METADATA = ValidationMetadata()
