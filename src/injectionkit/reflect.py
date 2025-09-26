import inspect
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter

__all__ = [
    "Parameter",
    "ComplicatedParameterError",
    "UndefinedParameterError",
    "RedefinedParameterError",
    "ProxyInvoker",
    "Injective",
    "injective_of",
]


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
    returns: type

    def invoker(self) -> ProxyInvoker:
        return ProxyInvoker(self.obj, self.parameters)


def injective_of(obj: object) -> Injective:
    if isinstance(obj, type):
        return _parse_callable(obj.__init__, alternate=obj)
    elif isinstance(obj, Callable):
        return _parse_callable(obj)  # pyright: ignore[reportUnknownArgumentType]
    raise TypeError(f"Cannot create functor from {obj}")


def _parse_callable(obj: Callable[..., object], alternate: Callable[..., object] | None = None) -> Injective:
    signature = inspect.signature(obj)
    parameters: list[Parameter] = []
    for parameter in signature.parameters.values():
        if parameter.name == "self":
            continue
        parameters.append(parameter)
    return Injective(alternate if alternate else obj, parameters, signature.return_annotation)
