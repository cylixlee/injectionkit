from typing import Annotated

from injectionkit.reflect.types import ConcreteType, Type, typeof


def test_typeof() -> None:
    # Concrete types.
    assert typeof(int) == Type(ConcreteType(int, []), set())
    assert typeof(list[int]) == Type(
        ConcreteType(list, [ConcreteType(int, [])]),
        set(),
    )
    assert typeof(tuple[int, str]) == Type(
        ConcreteType(
            tuple,
            [
                ConcreteType(int, []),
                ConcreteType(str, []),
            ],
        ),
        set(),
    )
    assert typeof(list[list[str]]) == Type(
        ConcreteType(
            list,
            [
                ConcreteType(
                    list,
                    [ConcreteType(str, [])],
                )
            ],
        ),
        set(),
    )

    # Annotated types.
    assert typeof(Annotated[int, "int"]) == Type(
        ConcreteType(int, []),
        {"int"},
    )
    assert typeof(Annotated[Annotated[int, "nested"], "int"]) == Type(
        ConcreteType(int, []),
        {"int", "nested"},
    )
    assert typeof(Annotated[list[int], "generic"]) == Type(
        ConcreteType(
            list,
            [ConcreteType(int, [])],
        ),
        {"generic"},
    )
