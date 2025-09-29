from injectionkit import App, Consumer, Provider, Supplier


def test_app() -> None:
    app = App(Supplier(42))
    final_answer = app.resolve(int)
    assert final_answer == 42


def test_resolve_self() -> None:
    def name() -> str:
        return "Cylix Lee"

    def some_routine(app: App) -> None:
        app.add(Supplier(23))

    def check(name: str, age: int) -> None:
        assert name == "Cylix Lee"
        assert age == 23

    App(
        Provider(name),
        Consumer(some_routine),
        Consumer(check),
    ).run()
