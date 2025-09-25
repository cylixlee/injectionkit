from abc import ABC
from dataclasses import dataclass

__all__ = ["Option", "Provider", "Supplier"]


class Option(ABC): ...


@dataclass(frozen=True)
class Provider(Option):
    component: type
    annotation: type | None = None
    singleton: bool = False


@dataclass(frozen=True)
class Supplier(Option):
    instance: object
    annotation: type | None = None
