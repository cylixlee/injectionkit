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
