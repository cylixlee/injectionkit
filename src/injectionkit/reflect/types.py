import typing
from dataclasses import dataclass

__all__ = [
    "ConcreteType",
    "Type",
    "UnreflectableTypeError",
    "InvalidLabelTypeError",
    "typeof",
    "InvalidAnnotatedTypeError",
]


@dataclass(frozen=True)
class ConcreteType(object):
    constructor: type
    parameters: list["ConcreteType"]


@dataclass(frozen=True)
class Type(object):
    concrete: ConcreteType
    labels: set[str]


class UnreflectableTypeError(Exception):
    invalid_type: object

    def __init__(self, invalid_type: object) -> None:
        super().__init__(f"Unable to reflect type: `{invalid_type}`")
        self.invalid_type = invalid_type


class InvalidLabelTypeError(Exception):
    invalid_label_type: object

    def __init__(self, invalid_label_type: object) -> None:
        super().__init__(f"Invalid label type: `{invalid_label_type}`")
        self.invalid_label_type = invalid_label_type


def typeof(annotation: object, exist_labels: set[str] | None = None) -> Type:
    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        # Annotated type
        #
        # The nested annotated type is automatically flattened. e.g. `Annotated[Annotated[int, "foo"], "bar"]` is
        # flattened to `Annotated[int, "foo", "bar"]`. Thus, we just need to parse the first argument as the concrete
        # type, and the rest as labels.
        args = typing.get_args(annotation)
        concrete = _concrete_typeof(args[0])
        for label in args[1:]:
            if not isinstance(label, str):
                raise InvalidLabelTypeError(label)
        labels = set(args[1:])
        if exist_labels is not None:
            labels |= exist_labels
        return Type(concrete, labels)
    else:
        return Type(_concrete_typeof(annotation), exist_labels or set())


class InvalidAnnotatedTypeError(Exception):
    invalid_annotated_type: object

    def __init__(self, invalid_annotated_type: object) -> None:
        super().__init__(f"Invalid annotated type: `{invalid_annotated_type}`")
        self.invalid_annotated_type = invalid_annotated_type


def _concrete_typeof(annotation: object) -> ConcreteType:
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is None:
        # Simple type
        #
        # e.g. `int`, `str`. No labels, no generics, just return it as is.
        if not isinstance(annotation, type):
            raise UnreflectableTypeError(annotation)
        return ConcreteType(annotation, [])
    else:
        # Generic type
        #
        # e.g. `tuple[int, str]`, `list[str]`. Recursively call `_concrete_typeof` to parse the generic parameters
        # before returning the concrete type.
        #
        # We do not support nested Annotated types in concrete types. For example, `list[Annotated[int, "label"]]` is
        # not allowed. To resolve multiple ints with label "label", use `Annotated[list[int], "label"]` instead.
        if origin is typing.Annotated:
            raise InvalidAnnotatedTypeError(typing.get_type_hints(annotation, include_extras=True))
        return ConcreteType(origin, [_concrete_typeof(arg) for arg in args])
