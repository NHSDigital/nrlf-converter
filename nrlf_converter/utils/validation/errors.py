from __future__ import annotations

from contextlib import contextmanager


class FieldNotFound(Exception):
    pass


class TypeMismatch(Exception):
    pass


class InvalidValue(Exception):
    pass


class InconsistentOptionalField(Exception):
    pass


class UnexpectedField(Exception):
    pass


def _tab_items(items: list[str]) -> list[str]:
    return [f"  {item}" for item in items]


class ValidationError(Exception):
    def __init__(self, message: str, notes: list[str] = []):
        self.message = message
        self.notes = notes
        super().__init__(message)

    def __str__(self):
        return "\n".join(("", self.message, *reversed(_tab_items(self.notes))))


VALIDATION_ERRORS = (
    FieldNotFound,
    TypeMismatch,
    InvalidValue,
    InconsistentOptionalField,
    UnexpectedField,
)


@contextmanager
def handle_validation_errors(obj, field):
    try:
        yield
    except VALIDATION_ERRORS as exc:
        raise ValidationError(
            message=f"'{type(exc).__name__}' encountered on '{type(obj).__name__}.{field}': {str(exc)}"
        ) from None
    except ValidationError as exc:
        message = exc.message
        exc.message = f"Error validating property '{type(obj).__name__}.{field}':"
        exc.notes = _tab_items(exc.notes)
        exc.notes.append(message)
        raise exc from None
