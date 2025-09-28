from abc import ABC, abstractmethod
from typing import Annotated

from typing_extensions import override

from injectionkit import App, Consumer, Provider, Supplier


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


def test_app() -> None:
    def hello(greeter: Greeter) -> None:
        assert greeter.greet() == "Hello, world!"

    App(
        Provider(Student, Greeter),
        Consumer(hello),
    ).run()


def test_multi() -> None:
    def hello(greeter: list[Greeter]) -> None:
        # No `list[Greeter]` registered directly, trying to resolve multiple `Greeter`s
        assert len(greeter) == 2
        assert greeter[0].greet() == "Hello, Cylix!"
        assert greeter[1].greet() == "Hello, world!"

    App(
        Provider(Student, Greeter),
        Supplier(CustomGreeter("Cylix"), Greeter),  # Suppliers are always prior to providers.
        Consumer(hello),
    ).run()


def test_labels() -> None:
    def functor_factory() -> Annotated[Greeter, "a", "b"]:
        return Student()

    def hello(a: Annotated[Greeter, "a"], b: Annotated[Greeter, "b"]) -> None:
        assert a.greet() == "Hello, world!"
        assert b.greet() == "Hello, world!"

    App(
        Provider(functor_factory),
        Consumer(hello),
    ).run()
