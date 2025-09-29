from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import TypeAlias

from .reflect import ConcreteType, signatureof, typeof

__all__ = ["InvalidProviderFactoryError", "Provider", "Supplier", "Consumer", "Option"]


class InvalidProviderFactoryError(Exception):
    """Signal that a provider factory is not callable or lacks a return type.

    Raised when a provider's factory attribute cannot be invoked or when its signature does not declare a concrete
    return annotation, preventing the container from determining which dependency it produces.

    Args:
        factory: Object that failed validation as a provider factory.
    """

    _factory: object

    def __init__(self, factory: object) -> None:
        super().__init__(f"Invalid provider factory: {factory}")
        self._factory = factory


@dataclass(frozen=True)
class Provider(object):
    """Describe a deferred dependency provider.

    Wraps a factory callable or explicit regard type, supports singleton semantics, and exposes reflective helpers that
    the container uses to determine the concrete type and labels produced by the provider.

    Attributes:
        factory: Callable responsible for building dependency instances.
        regard: Optional type annotation that overrides reflection on the factory signature.
        singleton: Flag indicating whether the provider should reuse a cached instance.
    """

    factory: object
    regard: object | None = None
    singleton: bool = False

    @property
    @cache
    def concrete_type(self) -> ConcreteType:
        """Return the concrete type produced by the provider.

        If a `regard` annotation is provided it takes precedence over signature inspection; otherwise the factory's
        return annotation is reflected to obtain the target concrete type.

        Returns:
            ConcreteType describing the dependency constructed by the provider.

        Raises:
            InvalidProviderFactoryError: If the provider lacks a concrete return annotation.
        """
        if self.regard is not None:
            regard_type = typeof(self.regard)
            return regard_type.concrete
        else:
            factory_signature = signatureof(self.factory)
            if factory_signature.returns is None:
                raise InvalidProviderFactoryError(self.factory)
            return factory_signature.returns.concrete

    @property
    @cache
    def labels(self) -> set[str]:
        """Return the label set associated with this provider.

        Mirrors the behaviour of `concrete_type` but extracts the labels either from the `regard` annotation or from the
        factory return annotation so the container can match consumers on label subsets.

        Returns:
            Set of string labels tied to the provider's output.

        Raises:
            InvalidProviderFactoryError: If the provider lacks a concrete return annotation.
        """
        if self.regard is not None:
            regard_type = typeof(self.regard)
            return regard_type.labels
        else:
            factory_signature = signatureof(self.factory)
            if factory_signature.returns is None:
                raise InvalidProviderFactoryError(self.factory)
            return factory_signature.returns.labels


@dataclass(frozen=True)
class Supplier(object):
    """Represent an eager dependency supplier.

    Encapsulates a pre-built instance and optional regard annotation, enabling the container to resolve dependencies
    without invoking a factory.

    Attributes:
        instance: Concrete object supplied to the container.
        regard: Optional annotation describing the instance for reflection.
    """

    instance: object
    regard: object | None = None

    @property
    @cache
    def labels(self) -> set[str]:
        """Return the label set carried by the supplier.

        Extracts labels from the optional `regard` annotation or returns an empty set when the supplier relies solely on
        the instance type.

        Returns:
            Set of labels associated with the supplied instance.
        """
        if self.regard is not None:
            regard_type = typeof(self.regard)
            return regard_type.labels
        return set()  # instance cannot carry any label

    @property
    @cache
    def concrete_type(self) -> ConcreteType:
        """Return the concrete type represented by the supplier.

        Prioritises the explicit `regard` annotation when present, otherwise reflects the runtime type of the provided
        instance.

        Returns:
            ConcreteType describing the supplied instance.
        """
        if self.regard is not None:
            regard_type = typeof(self.regard)
            return regard_type.concrete
        # instance cannot carry any labels.
        return typeof(type(self.instance)).concrete


@dataclass(frozen=True)
class Consumer(object):
    """Describe a callable that expects dependencies to be injected.

    Stores the functor to be executed so the application can resolve its parameters and inject dependencies at runtime.

    Attributes:
        functor: Callable executed during application runtime.
    """

    functor: Callable[..., None]


Option: TypeAlias = Provider | Supplier | Consumer
