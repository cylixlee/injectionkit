import inspect
from inspect import Parameter
from typing import Generic, TypeVar, final

from .option import Option, Provider, Supplier

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


@final
class App(object):
    _providers: _ResolutionContainer[Provider]
    _instances: _ResolutionContainer[object]

    def __init__(self, *options: Option) -> None:
        self._providers = _ResolutionContainer[Provider]()
        self._instances = _ResolutionContainer[object]()
        for option in options:
            if isinstance(option, Provider):
                self._providers.register(_annotation_of(option), option)
            elif isinstance(option, Supplier):
                self._instances.register(_annotation_of(option), option.instance)
            else:
                raise TypeError(f"Unsupported option type: {type(option)}")

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
        args: list[object] = []
        kwargs: dict[str, object] = {}
        for name, parameter in parameters.items():
            if parameter.kind == Parameter.VAR_KEYWORD:
                raise ValueError(f"VAR_KEYWORD parameter {name} in {provider.component} is not supported")

            argument: object | list[object] = None
            if parameter.annotation not in self:
                if parameter.default is not Parameter.empty:
                    argument = parameter.default
                else:
                    raise ValueError(f"Missing argument {name} of {provider.component}")
            else:
                argument = self._resolve(parameter.annotation)

            if parameter.kind == Parameter.VAR_POSITIONAL:
                if not isinstance(argument, list):
                    raise ValueError(
                        f"Argument {name} of {provider.component} should be resolved as multiple instances"
                    )
                args.extend(argument)  # pyright: ignore[reportUnknownArgumentType]
            elif parameter.kind == Parameter.POSITIONAL_ONLY:
                args.append(argument)
            else:
                kwargs[name] = argument

        instance = provider.component(*args, **kwargs)
        if provider.singleton:
            self._instances.register(_annotation_of(provider), instance)
        return instance
