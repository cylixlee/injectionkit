from types import GenericAlias
from typing import TypeAlias

StrList: TypeAlias = list[str]


def test_generic() -> None:
    assert isinstance(str, type)
    assert isinstance(list, type)
    assert StrList == list[str]
    assert isinstance(StrList, GenericAlias)
    assert isinstance(type(StrList), type)
