from dataclasses import dataclass
from typing import Annotated

from injectionkit import App, Consumer, Provider, Supplier


@dataclass(frozen=True)
class Person(object):
    name: str
    age: int


def test_labels() -> None:
    """
    Demonstrating how to use labels to distinguish dependencies of the same type.
    """

    # A provider of `Person`.
    #
    # This function requires two annotated arguments: a `str` with label "name", and an `int` with label "age".
    # InjectionKit allows functions and constructors to depend on annotated parameters, when multiple `str`s are
    # provided, only those with the label "name" will be passed into this function.
    #
    # When multiple labels are required, for example, an `Annotated[str, "a", "b"]` is required, only those instances
    # CONTAINING the labels will be passed in. For example, an `Annotated[str, "a", "b", "c"]` will be passed in because
    # it CONTAINS "a" and "b".
    def born(name: Annotated[str, "name"], age: Annotated[int, "age"]) -> Person:
        return Person(name, age)

    # A provider of `str` with label "name".
    #
    # A dependency can declare the label of the returned value using an `Annotated` return type. The `Annotated` is from
    # the stdlib `typing` module, and it's compatible with the underlying type while making the type checker happy.
    #
    # This design is intuitive and makes minimal changes to the provider, while maintaining readability.
    def name() -> Annotated[str, "name"]:
        return "Cylix"

    # A consumer.
    #
    # It just checks the fields of the `Person` passed in.
    def check(person: Person) -> None:
        assert person.name == "Cylix"
        assert person.age == 23

    App(
        # Provides `Annotated[str, "name"]`
        Provider(name),
        # Supplies a `str`, which will NOT be used by `born`.
        Supplier("unrelated str"),
        # Supplies an `int`, which will NOT be used by `born`.
        Supplier(42),
        # Supplies an `Annotated[int, "age"]`.
        #
        # `Provider`s and `Supplier`s can specify the `regard=type`, to achieve polymorphism. The framework will see the
        # factory or instance as the way to retrieve the `regard` type instead of the concrete type.
        Supplier(23, regard=Annotated[int, "age"]),
        # A provider of `Person`, which requires two annotated arguments.
        #
        # `Provider(name)` and `Supplier(23, regard=Annotated[int, "age"])` will be passed in.
        Provider(born),
        # The check consumer.
        Consumer(check),
    ).run()


def test_multi_labels() -> None:
    """
    Demonstating how to use multiple labels.
    """

    # A consumer requiring multiple `str`s with label "a" and "b".
    #
    # Because we won't inject `list[str]` directly, the framework will try to resolve `str`s with the labels instead. As
    # we mentioned before, the `str`s CONTAINING "a" and "b" will be injected, which means a `str` with "a", "b", "c"
    # will be passed in, while one with only "a" won't.
    #
    # BTW, the `list[Annotated[...]]` form is not accepted by this framework. The `Annotated` annotation must be placed
    # at the very outside.
    def hello(names: Annotated[list[str], "a", "b"]) -> None:
        assert names == ["Cylix", "Lee"]

    App(
        Supplier("some random str", regard=Annotated[str, "a"]),  # does NOT contain "b". unused.
        Supplier("Cylix", regard=Annotated[str, "a", "b"]),  # CONTAINS "a" and "b", passed in.
        Supplier("Lee", regard=Annotated[str, "a", "b", "c"]),  # CONTAINS "a" and "b", passed in.
        Consumer(hello),
    ).run()
