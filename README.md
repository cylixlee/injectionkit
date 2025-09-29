# InjectionKit

Dependency Injection framework for Python.

This project is in development and issues and PRs are welcome. Please feel free to share if you've got any ideas or encountered with any problems.

- [InjectionKit](#injectionkit)
  - [Installing](#installing)
  - [Usage](#usage)
    - [Simple usage](#simple-usage)
    - [Compositions](#compositions)
    - [Multivalues](#multivalues)
    - [Labels](#labels)

## Installing

If you're using pip, you can install this package by
```shell
pip install injectionkit
```

you can also install it with your favourable package manager. For example, with [uv](https://docs.astral.sh/uv):

```shell
uv add injectionkit
```

at least Python 3.10 is required.

## Usage

This package is inspired by [Uber's fx](https://pkg.go.dev/go.uber.org/fx) library in Go, and it adopts similar usage. For example, you can use `Provider`, `Supplier` and `Consumer` to define dependencies and how to inject them, and use `App` to wire things up.

### Simple usage

```python
from injectionkit import App, Consumer, Provider


def test_simple() -> None:
    """
    The simplest usage of this library.
    """

    # A function returning a value can be used as a provider.
    #
    # If the function receives parameters, they will be analyzed and injected automatically, based on their type
    # annotations. The returned value will be registered as a dependency and resolved when needed.
    def message() -> str:
        return "Hello, world!"

    # A function receiving a value or some values can be used as a consumer.
    #
    # The parameters are analyzed and injected automatically, based on their type annotations. The returned value will
    # be ignored, since we don't expect a Consumer to provide something.
    def check(message: str) -> None:
        assert message == "Hello, world!"

    # The `App` class wires up all the options, including Providers, Suppliers and Consumers.
    #
    # The Providers and Suppliers are registered, and will only be called when needed. Contrararily, the Consumers are
    # called immediately when the App is `run`.
    #
    # The order of the Providers and Suppliers is not guaranteed because of the resolution procedure, but the Consumers
    # is called in the order they were passed into the App. To be more precise, even if the Consumers are passed in with
    # some Providers and Suppliers in between of them, the Providers and Suppliers will not be called until resolution,
    # while the Consumers will be called when `App.run()`.
    App(
        Provider(message),
        Consumer(check),
    ).run()
```

### Compositions
Compositions between dependencies are must-have:

```python
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
```

### Multivalues

You can inject values of the same type one-by-one, and resolve them at once.

```python
from injectionkit import App, Consumer, Provider, Supplier


def test_multivalues() -> None:
    """
    Demonstrates the multivalue resolution.
    """

    # A simple provider that produces a `str`.
    def last_name() -> str:
        return "Lee"

    # A consumer that consumes a list of `str`s.
    #
    # When no `list[str]` is provided, the framework tries to resolve `str`s, and make them a list. If there's no more
    # than 2 instances of `str`, the framework will raise a `MissingDependencyError`.
    #
    # This behavior is not performed if a `list[str]` dependency is provided.
    def check(name: list[str]) -> None:
        # NOTICE: "Cylix" supplied by `Supplier` is before the "Lee" provided by `Provider`.
        #
        # This is because the framework first searches the instances, which is supplied by the `Supplier`s. It will
        # continue to search the `Provider`s to avoid unexpected shadowing. If there's multiple values after searching,
        # they'll be stored into a list. This is the behavior of the `DependencyContainer`.
        assert name == ["Cylix", "Lee"]

    App(
        Provider(last_name),
        Supplier("Cylix"),
        Consumer(check),
    ).run()
```

### Labels

And, to distinguish values of the same type, you can use `Annotated` from stdlib `typing` module, and labels of `str` type.

```python
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
```

For more examples, see the [tests](tests/) folder.