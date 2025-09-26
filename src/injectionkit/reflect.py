import inspect
import typing
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter
from typing import Annotated

__all__ = [
    "is_annotated",
    "unpack_annotated",
    "ComplicatedParameterError",
    "UndefinedParameterError",
    "RedefinedParameterError",
    "ProxyInvoker",
    "Injective",
    "UnsupportedLabelTypeError",
    "injective_of",
]


def is_annotated(annotation: object) -> bool:
    return typing.get_origin(annotation) is Annotated


def unpack_annotated(annotation: object) -> tuple[type, list[object]]:
    arguments = typing.get_args(annotation)
    return arguments[0], list(arguments[1:])


class ComplicatedParameterError(Exception):
    obj: Callable[..., object]
    parameter: Parameter

    def __init__(self, obj: Callable[..., object], parameter: Parameter) -> None:
        super().__init__(
            f"Parameter `{parameter.name}` of `{obj.__qualname__}` is variable"
            + ", which is too complicated for the invoker"
        )
        self.obj = obj
        obj.__qualname__
        self.parameter = parameter


class UndefinedParameterError(Exception):
    obj: Callable[..., object]
    parameter: Parameter

    def __init__(self, obj: Callable[..., object], parameter: Parameter) -> None:
        super().__init__(f"Parameter `{parameter.name}` of object `{obj.__qualname__}` is not defined")
        self.obj = obj
        self.parameter = parameter


class RedefinedParameterError(Exception):
    obj: Callable[..., object]
    parameter: Parameter
    value_present: object
    value_new: object

    def __init__(
        self,
        obj: Callable[..., object],
        parameter: Parameter,
        value_present: object,
        value_new: object,
    ) -> None:
        super().__init__(
            f"Parameter `{parameter.name}` of object `{obj.__class__.__name__}` already has a value "
            + "(`{value_present}` <- `{value_new}`)"
        )
        self.obj = obj
        self.parameter = parameter
        self.value_present = value_present
        self.value_new = value_new


class ProxyInvoker(object):
    class empty: ...

    _object: Callable[..., object]
    _arguments: OrderedDict[Parameter, object]

    def __init__(self, obj: Callable[..., object], parameters: list[Parameter]) -> None:
        self._object = obj
        self._arguments = OrderedDict[Parameter, object]()
        for parameter in parameters:
            if parameter.kind == Parameter.VAR_POSITIONAL or parameter.kind == Parameter.VAR_KEYWORD:
                raise ComplicatedParameterError(obj, parameter)
            if parameter.default is Parameter.empty:
                self._arguments[parameter] = self.empty
            else:
                self._arguments[parameter] = parameter.default

    def argument(self, parameter: Parameter, value: object) -> None:
        if parameter not in self._arguments:
            raise UndefinedParameterError(self._object, parameter)
        if self._arguments[parameter] is not self.empty:
            raise RedefinedParameterError(self._object, parameter, self._arguments[parameter], value)
        self._arguments[parameter] = value

    def invoke(self) -> object:
        positional: list[object] = []
        keyword: dict[str, object] = {}
        for parameter, value in self._arguments.items():
            if value is self.empty:
                raise UndefinedParameterError(self._object, parameter)

            if parameter.kind == Parameter.POSITIONAL_ONLY:
                positional.append(value)
            else:
                keyword[parameter.name] = value
        return self._object(*positional, **keyword)


@dataclass(frozen=True)
class Injective(object):
    obj: Callable[..., object]
    parameters: list[Parameter]
    returns: object
    labels: list[str] | None = None

    def invoker(self) -> ProxyInvoker:
        return ProxyInvoker(self.obj, self.parameters)


class UnsupportedLabelTypeError(Exception):
    label_type: object

    def __init__(self, label_type: object):
        super().__init__(f"Unsupported label type: {label_type}")
        self.label_type = label_type


def injective_of(obj: object, labels: list[str] | None = None) -> Injective:
    if is_annotated(obj):
        # Annotated type
        #
        # For annotated types (e.g. `Annotated[Klass, "label"]`), we just unpack the underlying type and the metadata
        # (labels), and create an injective object with the underlying type and the labels.
        underlying, metadata = unpack_annotated(obj)
        for metadatum in metadata:
            if not isinstance(metadatum, str):
                raise UnsupportedLabelTypeError(type(metadatum))
        return injective_of(underlying, metadata)  # pyright: ignore[reportArgumentType]
    elif isinstance(obj, type):
        # Classes
        #
        # We use the constructor (`__init__`) of the class as the underlying callable, while calling with the class
        # name. This is the Pythonic way to create an instance of a class.
        return _parse_callable(obj.__init__, labels, klass=obj)
    elif isinstance(obj, Callable):
        # Functions
        #
        # Functions can be used to inject dependencies, too. It takes several parameters and returns a value.
        return _parse_callable(obj, labels)  # pyright: ignore[reportUnknownArgumentType]
    raise TypeError(f"Cannot create functor from {obj}")


def _parse_callable(obj: Callable[..., object], labels: list[str] | None, klass: type | None = None) -> Injective:
    if labels is None:
        labels = []

    # Parse parameters
    signature = inspect.signature(obj)
    parameters: list[Parameter] = []
    for parameter in signature.parameters.values():
        if parameter.name == "self":
            continue
        parameters.append(parameter)

    if not klass:
        # Parse return type. Return type annotation is accepted
        returns = signature.return_annotation
        if is_annotated(returns):
            returns, returns_labels = unpack_annotated(returns)
            for label in returns_labels:
                if not isinstance(label, str):
                    raise UnsupportedLabelTypeError(type(label))
            labels = [*labels, *returns_labels]  # pyright: ignore[reportAssignmentType]
    else:
        returns = klass

    return Injective(klass if klass else obj, parameters, returns, labels)
