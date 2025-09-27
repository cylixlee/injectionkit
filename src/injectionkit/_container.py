from collections.abc import Callable
from typing import final

from .option import Provider
from .reflect import ConcreteType, Parameter, ParameterKind, Unspecified, signatureof


class Instantiator(object):
    _factory: Callable[..., object]
    _parameters: dict[str, Parameter]
    _arguments: dict[str, object]

    def __init__(self, factory: Callable[..., object]) -> None:
        self._factory = factory
        self._parameters = {}
        self._arguments = {}

        signature = signatureof(factory)
        for parameter in signature.parameters:
            self._parameters[parameter.name] = parameter
            if parameter.default_value is not None:
                self._arguments[parameter.name] = parameter.default_value
            else:
                self._arguments[parameter.name] = Unspecified

    def argument(self, name: str, value: object) -> None:
        if name not in self._arguments:
            raise AttributeError(f"Unknown parameter: {name}")
        if self._arguments[name] is not Unspecified:
            raise AttributeError(f"Parameter already set: {name}")
        self._arguments[name] = value

    def instantiate(self) -> object:
        args = []
        kwargs = {}
        for name, argument in self._arguments.items():
            if argument is Unspecified:
                raise AttributeError(f"Parameter not set: {name}")
            parameter = self._parameters[name]
            if parameter.kind == ParameterKind.positional:
                args.append(argument)
            else:
                kwargs[name] = argument
        return self._factory(*args, **kwargs)


@final
class DependencyContainer(object):
    _providers: dict[ConcreteType, dict[str, list[Provider]]]
    _instances: dict[ConcreteType, dict[str, list[object]]]

    def __init__(self) -> None:
        self._providers = {}
        self._instances = {}
