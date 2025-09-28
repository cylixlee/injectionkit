from collections.abc import Callable, Iterable
from typing import Generic, TypeVar, final

from .option import InvalidProviderFactoryError, Provider, Supplier
from .reflect import ConcreteType, Parameter, ParameterKind, Unspecified, signatureof, typeof


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


_T = TypeVar("_T")


class _Labeled(Generic[_T]):
    value: _T
    labels: set[str]

    def __init__(self, value: _T, labels: Iterable[str]) -> None:
        self.value = value
        self.labels = set(labels)

    def __contains__(self, labels: Iterable[str]) -> bool:
        return self.labels.issuperset(labels)


class MissingDependencyError(Exception):
    concrete: ConcreteType
    labels: set[str]

    def __init__(self, concrete: ConcreteType, labels: set[str]) -> None:
        super().__init__(f"Missing dependency for `{concrete}`, labels: `{labels}`")
        self.concrete = concrete
        self.labels = labels


@final
class DependencyContainer(object):
    _providers: dict[ConcreteType, list[_Labeled[Provider]]]
    _instances: dict[ConcreteType, list[_Labeled[object]]]

    def __init__(self) -> None:
        self._providers = {}
        self._instances = {}

    def register(self, option: Provider | Supplier) -> None:
        if isinstance(option, Provider):
            if option.concrete_type not in self._providers:
                self._providers[option.concrete_type] = [_Labeled(option, option.labels)]
            else:
                self._providers[option.concrete_type].append(_Labeled(option, option.labels))
        else:  # Supplier
            if option.concrete_type not in self._instances:
                self._instances[option.concrete_type] = [_Labeled(option.instance, option.labels)]
            else:
                self._instances[option.concrete_type].append(_Labeled(option.instance, option.labels))

    def resolve(self, annotation: object) -> object | list[object]:
        typ = typeof(annotation)
        return self._instantiate(typ.concrete, typ.labels)

    def _instantiate(self, concrete: ConcreteType, labels: set[str]) -> object | list[object]:
        candidates: list[object] = []
        if concrete in self._instances:
            for labeled_instance in self._instances[concrete]:
                if labels in labeled_instance:
                    candidates.append(labeled_instance.value)
        if concrete in self._providers:
            providers: list[Provider] = []
            for labeled_provider in self._providers[concrete]:
                if labels in labeled_provider:
                    providers.append(labeled_provider.value)
            for provider in providers:
                if not callable(provider.factory):
                    raise InvalidProviderFactoryError(provider.factory)
                signature = signatureof(provider.factory)
                instantiator = Instantiator(provider.factory)
                for parameter in signature.parameters:
                    try:
                        argument = self._instantiate(parameter.typ.concrete, parameter.typ.labels)
                        instantiator.argument(parameter.name, argument)
                    except MissingDependencyError:
                        if parameter.default_value is Unspecified:
                            raise
                candidates.append(instantiator.instantiate())
        if not candidates:
            raise MissingDependencyError(concrete, labels)
        if len(candidates) == 1:
            return candidates[0]
        return candidates
