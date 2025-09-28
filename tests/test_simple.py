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
