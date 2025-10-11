from typing import final

from ._container import DependencyContainer, Instantiator, MissingDependencyError
from ._option import Consumer, Option, Supplier
from .reflect import Unspecified, signatureof

__all__ = ["App", "runApp"]


@final
class App(object):
    """Coordinate dependency options with consumer execution.

    The application builds a dependency graph from the supplied options, keeps track of registered consumers, and
    resolves their inputs when `run` executes.
    """

    _container: DependencyContainer
    _consumers: list[Consumer]

    def __init__(self, *options: Option) -> None:
        """Populate the application with the provided dependency options.

        The constructor processes each option immediately, registering providers or suppliers and remembering consumers
        for later execution.

        Args:
            *options: Provider, supplier, or consumer instances that describe how dependencies should be built or
                consumed.

        Returns:
            None
        """
        self._container = DependencyContainer()
        self._consumers = []
        self.add(Supplier(self))
        self.add(*options)

    def add(self, *options: Option) -> None:
        """Register additional dependency options after initialization.

        The method processes each option immediately so new providers and suppliers become available to consumers while
        new consumers are queued for later execution when `run` is called.

        Args:
            *options: Provider, supplier, or consumer instances to merge into the application.

        Returns:
            None
        """
        for option in options:
            if isinstance(option, Consumer):
                self._consumers.append(option)
            else:
                self._container.register(option)

    def resolve(self, annotation: object) -> object:
        """
        Resolves a dependency.

        Args:
            annotation: The dependency annotation to resolve.
        """
        return self._container.resolve(annotation)

    def run(self) -> None:
        """Resolve dependencies and invoke every registered consumer.

        For each consumer the application determines required inputs, initializes them from registered dependencies or
        defaults, injects the resulting values, and finally executes the callable.

        Returns:
            None

        Raises:
            MissingDependencyError: If a consumer requires a dependency that is not registered and lacks a default
                value.
        """
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
                    raise
                    # # If it's not a list, then this is indeed a missing dependency.
                    # if parameter.typ.concrete.constructor is not list:
                    #     raise

                    # # Or, if it's a list, try to instantiate its inner type and returns them or it as a list
                    # inner_type = parameter.typ.concrete.parameters[0]
                    # argument = self._container.instantiate(inner_type, parameter.typ.labels)
                    # if not isinstance(argument, list):
                    #     raise  # No MULTIPLE values found.
                    # instantiator.argument(parameter.name, argument)
            _ = instantiator.instantiate()


def runApp(*options: Option) -> None:
    App(*options).run()
