from dataclasses import dataclass
from typing import Callable, TypeAlias

__all__ = ["Provider", "Supplier", "Option"]


@dataclass(frozen=True)
class Provider(object):
    component: type
    annotation: type | None = None
    singleton: bool = False


@dataclass(frozen=True)
class Supplier(object):
    instance: object
    annotation: type | None = None


@dataclass(frozen=True)
class Consumer(object):
    func: Callable[..., None]


Option: TypeAlias = Provider | Supplier | Consumer
