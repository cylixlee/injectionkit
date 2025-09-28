from typing import final

from ._container import DependencyContainer, Instantiator, MissingDependencyError
from ._option import Consumer, Option
from .reflect import Unspecified, signatureof

__all__ = ["App"]


@final
class App(object):
    _container: DependencyContainer
    _consumers: list[Consumer]

    def __init__(self, *options: Option) -> None:
        self._container = DependencyContainer()
        self._consumers = []
        for option in options:
            if isinstance(option, Consumer):
                self._consumers.append(option)
            else:
                self._container.register(option)

    def run(self) -> None:
        for consumer in self._consumers:
            signature = signatureof(consumer.functor)
            instantiator = Instantiator(consumer.functor)
            for parameter in signature.parameters:
                try:
                    argument = self._container.instantiate(parameter.typ.concrete, parameter.typ.labels)
                    instantiator.argument(parameter.name, argument)
                except MissingDependencyError:
                    # Skip it if a default value is provided
                    if parameter.default_value is not Unspecified:
                        continue
                    # If it's not a list, then this is indeed a missing dependency.
                    if parameter.typ.concrete.constructor is not list:
                        raise

                    # Or, if it's a list, try to instantiate its inner type and returns them or it as a list
                    inner_type = parameter.typ.concrete.parameters[0]
                    argument = self._container.instantiate(inner_type, parameter.typ.labels)
                    if not isinstance(argument, list):
                        argument = [argument]
                    instantiator.argument(parameter.name, argument)  # pyright: ignore[reportUnknownArgumentType]
            _ = instantiator.instantiate()
