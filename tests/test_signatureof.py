from typing import Annotated

from injectionkit.reflect import ConcreteType, Parameter, ParameterKind, Signature, Type, Unspecified, signatureof


def simple(a: str, /, b: int = 10) -> tuple[int, str]: ...  # pyright: ignore[reportUnusedParameter]
def annotated_returns(a: str) -> Annotated[str, "label"]: ...  # pyright: ignore[reportUnusedParameter]
def annotated_parameter(a: Annotated[str, "label"]) -> str: ...  # pyright: ignore[reportUnusedParameter]


def test_signatureof() -> None:
    simple_signature = Signature(
        [
            Parameter(Type(ConcreteType(str, []), set()), "a", Unspecified, ParameterKind.positional),
            Parameter(Type(ConcreteType(int, []), set()), "b", 10, ParameterKind.keyword),
        ],
        Type(
            ConcreteType(
                tuple,
                [
                    ConcreteType(int, []),
                    ConcreteType(str, []),
                ],
            ),
            set(),
        ),
    )

    annotated_returns_signature = Signature(
        [Parameter(Type(ConcreteType(str, []), set()), "a", Unspecified, ParameterKind.keyword)],
        Type(ConcreteType(str, []), {"label"}),
    )

    annotated_parameter_signature = Signature(
        [Parameter(Type(ConcreteType(str, []), {"label"}), "a", Unspecified, ParameterKind.keyword)],
        Type(ConcreteType(str, []), set()),
    )

    assert signatureof(simple) == simple_signature
    assert signatureof(annotated_returns) == annotated_returns_signature
    assert signatureof(annotated_parameter) == annotated_parameter_signature
