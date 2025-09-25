import inspect
from collections.abc import Callable
from inspect import Parameter
from typing import Generic, TypeVar, final

from .option import Consumer, Option, Provider, Supplier

__all__ = ["App"]


_T = TypeVar("_T")


class _ResolutionContainer(Generic[_T], object):
    _mapping: dict[type, _T | list[_T]]

    def __init__(self) -> None:
        self._mapping = {}

    def __contains__(self, key: type) -> bool:
        return key in self._mapping

    def register(self, key: type, value: _T) -> None:
        if key in self._mapping:
            target = self._mapping[key]
            if isinstance(target, list):
                target.append(value)
            else:
                self._mapping[key] = [target, value]
        else:
            self._mapping[key] = value

    def resolve(self, key: type) -> _T | list[_T]:
        if key not in self._mapping:
            raise KeyError(f"Key {key} not found")
        return self._mapping[key]


def _annotation_of(option: Provider | Supplier) -> type:
    if option.annotation is not None:
        return option.annotation
    else:
        if isinstance(option, Provider):
            return option.component
        else:
            return type(option.instance)


class _ProxyInvoker(object):
    _positional: list[object]
    _keyword: dict[str, object]
    _callable: Callable[..., object]

    def __init__(self, callable: Callable[..., object]) -> None:
        self._callable = callable
        self._positional = []
        self._keyword = {}

    def argument(self, parameter: Parameter, value: object | list[object]) -> None:
        if parameter.kind == Parameter.VAR_KEYWORD:
            raise TypeError(f"Unsupported VAR_POSITIONAL parameter {parameter.name} of {self._callable}")

        if parameter.kind == Parameter.POSITIONAL_ONLY:
            self._positional.append(value)
        elif parameter.kind == Parameter.VAR_POSITIONAL:
            if not isinstance(value, list):
                raise TypeError(f"Expected list for VAR_POSITIONAL parameter {parameter.name} of {self._callable}")
            self._positional.extend(value)  # pyright: ignore[reportUnknownArgumentType]
        else:
            if parameter.name in self._keyword:
                raise ValueError(f"Duplicate keyword argument {parameter.name} of {self._callable}")
            self._keyword[parameter.name] = value

    def invoke(self) -> object:
        return self._callable(*self._positional, **self._keyword)


@final
class App(object):
    _providers: _ResolutionContainer[Provider]
    _instances: _ResolutionContainer[object]
    _consumers: list[Consumer]

    def __init__(self, *options: Option) -> None:
        self._providers = _ResolutionContainer[Provider]()
        self._instances = _ResolutionContainer[object]()
        self._consumers = []
        for option in options:
            if isinstance(option, Provider):
                self._providers.register(_annotation_of(option), option)
            elif isinstance(option, Supplier):
                self._instances.register(_annotation_of(option), option.instance)
            else:
                self._consumers.append(option)

    def run(self) -> None:
        consumer_proxies: list[_ProxyInvoker] = []
        for consumer in self._consumers:
            parameters = inspect.signature(consumer.func).parameters
            proxy = _ProxyInvoker(consumer.func)
            for parameter in parameters.values():
                proxy.argument(parameter, self._resolve(parameter.annotation))
            consumer_proxies.append(proxy)

        for consumer_proxy in consumer_proxies:
            _ = consumer_proxy.invoke()

    def __contains__(self, key: type) -> bool:
        return key in self._instances or key in self._providers

    def _resolve(self, key: type) -> object | list[object]:
        if key in self._instances:
            return self._instances.resolve(key)
        if key not in self._providers:
            raise KeyError(f"No provider for {key}")

        provider = self._providers.resolve(key)
        if isinstance(provider, list):
            return [self._instantiate(p) for p in provider]
        return self._instantiate(provider)

    def _instantiate(self, provider: Provider) -> object:
        parameters = inspect.signature(provider.component.__init__).parameters
        constructor_proxy = _ProxyInvoker(provider.component)
        for name, parameter in parameters.items():
            if name == "self":
                continue

            if parameter.annotation not in self:
                if parameter.default is not Parameter.empty:
                    constructor_proxy.argument(parameter, parameter.default)
                else:
                    raise ValueError(f"Missing dependency for {name} of {provider.component}")
            else:
                constructor_proxy.argument(parameter, self._resolve(parameter.annotation))
        instance = constructor_proxy.invoke()
        if provider.singleton:
            self._instances.register(_annotation_of(provider), instance)
        return instance
