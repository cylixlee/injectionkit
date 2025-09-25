import inspect
from collections.abc import Callable


def test_callable_parameters() -> None:
    def greet(name: str, age: int) -> None:
        print(f"Hello, {name}! You are {age} years old.")

    parameters = inspect.signature(greet).parameters
    assert parameters["name"].annotation is str
    assert parameters["age"].annotation is int


def test_intermediate_callable_parameters() -> None:
    def proxy_test(c: Callable[..., object]) -> None:
        signature = inspect.signature(c)
        parameters = signature.parameters
        assert parameters["name"].annotation is str
        assert parameters["age"].annotation is int
        assert signature.return_annotation is float

    def greet(name: str, age: int) -> float:
        print(f"Hello, {name}! You are {age} years old.")
        return 114.514

    proxy_test(greet)
