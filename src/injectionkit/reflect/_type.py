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


@dataclass(frozen=True, unsafe_hash=True)
class ConcreteType(object):
    """Describe a nominal type along with its generic parameters.

    Represents the fully resolved constructor for a dependency along with any nested parameter types extracted from
    typing annotations.

    Attributes:
        constructor: Base Python type that should be instantiated or matched.
        parameters: Frozen list of nested `ConcreteType` instances for generic parameters.
    """

    constructor: type
    parameters: tuple["ConcreteType", ...]


@dataclass(frozen=True, unsafe_hash=True)
class Type(object):
    """Represent a reflected type along with any associated labels.

    Couples the concrete type with a set of string labels that scope dependency resolution across providers and
    consumers.

    Attributes:
        concrete: Concrete type descriptor captured from annotations.
        labels: Set of string labels attached to the type.
    """

    concrete: ConcreteType
    labels: set[str]


class UnreflectableTypeError(Exception):
    """Signal that an annotation cannot be converted into a `ConcreteType`.

    Raised when the reflection logic encounters non-type objects or unsupported constructs that prevent type
    introspection.

    Args:
        invalid_type: Annotation that could not be reflected.
    """

    invalid_type: object

    def __init__(self, invalid_type: object) -> None:
        super().__init__(f"Unable to reflect type: `{invalid_type}`")
        self.invalid_type = invalid_type


class InvalidLabelTypeError(Exception):
    """Signal that an annotation contains labels of an unsupported type.

    Raised when annotations within `typing.Annotated` metadata use non-string labels, which would break the label
    matching system.

    Args:
        invalid_label_type: Label value that failed validation.
    """

    invalid_label_type: object

    def __init__(self, invalid_label_type: object) -> None:
        super().__init__(f"Invalid label type: `{invalid_label_type}`")
        self.invalid_label_type = invalid_label_type


def typeof(annotation: object, exist_labels: set[str] | None = None) -> Type:
    """Reflect an annotation into a `Type` with concrete structure and labels.

    Handles plain types, generic aliases, and `typing.Annotated` metadata while recursively parsing nested annotations
    to build complete type descriptors.

    Args:
        annotation: Type annotation to be reflected.
        exist_labels: Optional set of labels carried from the calling context.

    Returns:
        Type object that includes the resolved concrete representation and associated labels.

    Raises:
        InvalidLabelTypeError: If an annotated label is not a string.
        InvalidAnnotatedTypeError: If nested annotated types appear where they are not supported.
        UnreflectableTypeError: If the annotation cannot be converted into a type.
    """
    origin = typing.get_origin(annotation)
    if origin == typing.Annotated:
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
    """Signal that `typing.Annotated` was used in an unsupported position.

    Raised when nested annotated types appear inside concrete generic parameters, which would complicate the resolution
    model.

    Args:
        invalid_annotated_type: Annotation that violated the constraint.
    """

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
        return ConcreteType(annotation, ())
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
        return ConcreteType(origin, tuple(_concrete_typeof(arg) for arg in args))
