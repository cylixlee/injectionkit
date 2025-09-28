from abc import ABC, abstractmethod
from typing import Annotated

from typing_extensions import override

from injectionkit import DependencyContainer, Provider, Supplier


class Greeter(ABC):
    @abstractmethod
    def greet(self) -> str:
        raise NotImplementedError()


class Student(Greeter):
    def __init__(self) -> None:
        pass

    @override
    def greet(self) -> str:
        return "Hello, world!"


class CustomGreeter(Greeter):
    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    @override
    def greet(self) -> str:
        return f"Hello, {self._name}!"


def test_polymorphism() -> None:
    container = DependencyContainer()
    container.register(Provider(Student, regard=Greeter))
    greeter = container.resolve(Greeter)

    assert isinstance(greeter, Greeter)
    assert isinstance(greeter, Student)
    assert greeter.greet() == "Hello, world!"


def test_labeled() -> None:
    container = DependencyContainer()
    container.register(Supplier(CustomGreeter("Cylix"), regard=Annotated[Greeter, "first"]))
    container.register(Supplier(CustomGreeter("Lee"), regard=Annotated[Greeter, "last"]))

    first = container.resolve(Annotated[Greeter, "first"])
    last = container.resolve(Annotated[Greeter, "last"])
    assert isinstance(first, Greeter)
    assert isinstance(last, Greeter)
    assert isinstance(first, CustomGreeter)
    assert isinstance(last, CustomGreeter)
    assert first.greet() == "Hello, Cylix!"
    assert last.greet() == "Hello, Lee!"
