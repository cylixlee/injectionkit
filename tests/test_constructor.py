import inspect
from inspect import Parameter
from typing import no_type_check


def test_constructor_parameters() -> None:
    class SampleClass(object):
        inner_a: int
        inner_b: str

        def __init__(self, a: int, *, b: str = "") -> None:
            self.inner_a = a
            self.inner_b = b

    signature = inspect.signature(SampleClass.__init__).parameters
    assert signature["a"].name == "a"
    assert signature["a"].annotation is int
    assert signature["a"].default is Parameter.empty
    assert signature["a"].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert signature["b"].name == "b"
    assert signature["b"].annotation is str
    assert signature["b"].default == ""
    assert signature["b"].kind == Parameter.KEYWORD_ONLY


def test_positional_only() -> None:
    class PositionalOnly(object):
        a: int

        def __init__(self, a: int, /) -> None:
            self.a = a

    parameters = inspect.signature(PositionalOnly.__init__).parameters
    assert parameters["a"].name == "a"
    assert parameters["a"].annotation is int
    assert parameters["a"].default is Parameter.empty
    assert parameters["a"].kind == Parameter.POSITIONAL_ONLY


def test_positional_or_keyword() -> None:
    class PositionalOrKeyword(object):
        a: int

        def __init__(self, a: int) -> None:
            self.a = a

    parameters = inspect.signature(PositionalOrKeyword.__init__).parameters
    assert parameters["a"].name == "a"
    assert parameters["a"].annotation is int
    assert parameters["a"].default is Parameter.empty
    assert parameters["a"].kind == Parameter.POSITIONAL_OR_KEYWORD


def test_keyword_only() -> None:
    class KeywordOnly(object):
        a: int

        def __init__(self, *, a: int) -> None:
            self.a = a

    parameters = inspect.signature(KeywordOnly.__init__).parameters
    assert parameters["a"].name == "a"
    assert parameters["a"].annotation is int
    assert parameters["a"].default is Parameter.empty
    assert parameters["a"].kind == Parameter.KEYWORD_ONLY


def test_var_positional() -> None:
    class VarPositional(object):
        a: list[int]

        def __init__(self, *a: int) -> None:
            self.a = list(a)

    parameters = inspect.signature(VarPositional.__init__).parameters
    assert parameters["a"].name == "a"
    assert parameters["a"].annotation is int  # The annotation is the type of a single element.
    assert parameters["a"].default is Parameter.empty
    assert parameters["a"].kind == Parameter.VAR_POSITIONAL


def test_var_keyword() -> None:
    class VarKeyword(object):
        a: dict[str, int]

        def __init__(self, **a: int) -> None:  # The annotation is `dict[str, T]`, because keywords are always `str`s.
            self.a = dict(a)

    parameters = inspect.signature(VarKeyword.__init__).parameters
    assert parameters["a"].name == "a"
    assert parameters["a"].annotation is int  # The annotation is the type of a single element.
    assert parameters["a"].default is Parameter.empty
    assert parameters["a"].kind == Parameter.VAR_KEYWORD


@no_type_check
def test_instantiate() -> None:
    class Instantiate(object):
        positional: int
        positional_or_keyword: str
        keyword_only: bool

        def __init__(self, positional: int, /, positional_or_keyword: str, *, keyword_only: bool) -> None:
            self.positional = positional
            self.positional_or_keyword = positional_or_keyword
            self.keyword_only = keyword_only

    args = [1, "hello"]
    kwargs = {"keyword_only": True}
    obj = Instantiate(*args, **kwargs)
    assert obj.positional == 1
    assert obj.positional_or_keyword == "hello"
    assert obj.keyword_only is True
