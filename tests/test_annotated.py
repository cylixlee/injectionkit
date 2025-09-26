from typing import Annotated

from injectionkit import reflect


def test_class() -> None:
    class Student(object):
        pass

    klass = reflect.injective_of(Annotated[Student, "student"])
    assert klass.returns is Student
    assert klass.labels == ["student"]


def test_return_type() -> None:
    def goodbye() -> Annotated[str, "goodbye-message"]:
        return "Goodbye!"

    function = reflect.injective_of(goodbye)
    assert function.returns is str
    assert function.labels == ["goodbye-message"]
