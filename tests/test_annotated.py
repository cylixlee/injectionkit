from typing import Annotated

from injectionkit import reflect


def test_parameter() -> None:
    def hello(name: Annotated[str, "student-name"]) -> None:
        print(f"Hello, {name}!")

    function = reflect.injective_of(hello)
    assert reflect.is_annotated(function.parameters[0].annotation)
    assert reflect.unpack_annotated(function.parameters[0].annotation) == (str, ["student-name"])


def test_return_type() -> None:
    def goodbye() -> Annotated[str, "goodbye-message"]:
        return "Goodbye!"

    function = reflect.injective_of(goodbye)
    assert function.labels == ["goodbye-message"]
