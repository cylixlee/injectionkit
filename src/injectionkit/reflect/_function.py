import inspect
from dataclasses import dataclass
from enum import Enum, auto

from ._type import Type, typeof

__all__ = [
    "Unspecified",
    "ParameterKind",
    "Parameter",
    "Signature",
    "ComplicatedSignatureError",
    "signatureof",
]


class Unspecified:
    """Sentinel used to express that a parameter lacks an assigned value.

    This marker distinguishes between `None` defaults and genuinely unset values when reflecting function signatures and
    constructing instantiators.
    """

    ...


class ParameterKind(Enum):
    """Categorise reflected parameters by the way they accept values.

    Distinguishes positional-only parameters from keyword-capable ones so the instantiator can build positional and
    keyword arguments correctly.
    """

    positional = auto()
    keyword = auto()


@dataclass(frozen=True)
class Parameter(object):
    """Represent a single callable parameter in a reflected signature.

    Stores type metadata, defaults, and kind information to guide dependency injection when invoking factories or
    consumers.

    Attributes:
        typ: Fully reflected type associated with the parameter.
        name: Parameter identifier as declared on the callable.
        default_value: Value provided when the parameter is optional.
        kind: Indicates whether the parameter is positional or keyword-based.
    """

    typ: Type
    name: str
    default_value: object
    kind: ParameterKind


@dataclass(frozen=True)
class Signature(object):
    """Capture the reflected signature of a callable.

    Packages reflected parameters and optional return type so the container can resolve dependencies and reason about
    provider outputs.

    Attributes:
        parameters: Ordered list of reflected parameters.
        returns: Optional reflected return type, if annotated.
    """

    parameters: list[Parameter]
    returns: Type | None


class ComplicatedSignatureError(Exception):
    """Signal that a callable's signature is too dynamic to reflect safely.

    Raised when a parameter uses variadic constructs that the injector cannot reliably handle.

    Args:
        argument_name: Name of the unsupported parameter.
    """

    argument_name: str

    def __init__(self, argument_name: str) -> None:
        super().__init__(f"Argument `{argument_name}` is too complicated to get signature of")
        self.argument_name = argument_name


def signatureof(obj: object) -> Signature:
    """Reflect a callable or type into a structured signature.

    Accepts callables or classes, inspects parameter annotations, skips `self` parameters, validates that no variadic
    constructs are used, and returns a `Signature` describing inputs and the optional return type.

    Args:
        obj: Callable or class whose constructor should be reflected.

    Returns:
        Signature holding all reflected parameters and the optional return type.

    Raises:
        TypeError: If the provided object is not callable.
        ComplicatedSignatureError: If the callable uses unsupported variadic parameters.
    """
    returns: Type | None = None

    if isinstance(obj, type):
        returns = typeof(obj)
        obj = obj.__init__  # type: ignore
    if not callable(obj):
        raise TypeError(f"Expected a callable, got `{type(obj)}`")

    function_signature = inspect.signature(obj)

    # Parse parameters
    parameters: list[Parameter] = []
    for parameter in function_signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL or parameter.kind == inspect.Parameter.VAR_KEYWORD:
            raise ComplicatedSignatureError(parameter.name)
        if parameter.name == "self":
            continue

        parameter_type = typeof(parameter.annotation)
        default_value: object | Unspecified = Unspecified
        kind: ParameterKind = ParameterKind.keyword
        if parameter.default is not inspect.Parameter.empty:
            default_value = parameter.default
        if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
            kind = ParameterKind.positional
        parameters.append(Parameter(parameter_type, parameter.name, default_value, kind))

    if (
        returns is None
        and function_signature.return_annotation is not inspect.Parameter.empty
        and function_signature.return_annotation is not None
    ):
        returns = typeof(function_signature.return_annotation)
    return Signature(parameters, returns)
