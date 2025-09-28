from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import TypeAlias

from .reflect import ConcreteType, signatureof, typeof

__all__ = ["InvalidProviderFactoryError", "Provider", "Supplier", "Consumer", "Option"]


class InvalidProviderFactoryError(Exception):
    _factory: object

    def __init__(self, factory: object) -> None:
        super().__init__(f"Invalid provider factory: {factory}")
        self._factory = factory


@dataclass(frozen=True)
class Provider(object):
    factory: object
    regard: object | None = None
    singleton: bool = False

    @property
    @cache
    def concrete_type(self) -> ConcreteType:
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
    instance: object
    regard: object | None = None

    @property
    @cache
    def labels(self) -> set[str]:
        if self.regard is not None:
            regard_type = typeof(self.regard)
            return regard_type.labels
        return set()  # instance cannot carry any label

    @property
    @cache
    def concrete_type(self) -> ConcreteType:
        if self.regard is not None:
            regard_type = typeof(self.regard)
            return regard_type.concrete
        # instance cannot carry any labels.
        return typeof(type(self.instance)).concrete


@dataclass(frozen=True)
class Consumer(object):
    functor: Callable[..., None]


Option: TypeAlias = Provider | Supplier | Consumer
