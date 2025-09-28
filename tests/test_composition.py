from dataclasses import dataclass

from injectionkit import App, Consumer, Provider, Supplier


# Here we define a dataclass, whose constructor (`__init__()`) is automatically created, by the `@dataclass` decorator.
#
# To be more precise, the constructor signature is: `def __init__(self, name: str, age: int) -> None`.
@dataclass(frozen=True)
class Person(object):
    name: str
    age: int


def test_composition() -> None:
    """
    A usecase which shows how the framework wires things up.
    """

    # A simple function factory, which produces a `str`.
    def name() -> str:
        return "Cylix"

    # A simple consumer function, which requires a `Person`.
    def check(person: Person) -> None:
        assert person.name == "Cylix"
        assert person.age == 23

    App(
        # Provides a `str` to the framework through the function.
        Provider(name),
        # Supplies an `int` to the framework.
        #
        # Suppliers receives specific values (instances) rather than functions or classes. It just inject a value into
        # the framework.
        Supplier(23),
        # Provides a `Person` to the framework through the class name.
        #
        # Internally, InjectionKit will use the constuctor of this class to analyze and inject the dependencies. The
        # `Person` constructor requires a `str` and an `int` as arguments, the former is provided by the
        # `Provider(name)`, and the latter is supplied by `Supplier(23)`.
        #
        # When `singleton=True`, the `Person` instance will be cached in the framework after the first initialization.
        # When another consumer tries to consume a `Person`, the instance will be reused and the constructor will NOT be
        # called again.
        Provider(Person, singleton=True),
        # Consumes a `Person` from the framework.
        Consumer(check),
    ).run()
