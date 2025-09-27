from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

__all__ = ["Provider", "Supplier", "Consumer", "Option"]


@dataclass(frozen=True)
class Provider(object):
    factory: object
    regard: object = None
    singleton: bool = False


@dataclass(frozen=True)
class Supplier(object):
    instance: object
    regard: object = None


@dataclass(frozen=True)
class Consumer(object):
    functor: Callable[..., None]


Option: TypeAlias = Provider | Supplier | Consumer
