from injectionkit import App, Supplier


def test_app() -> None:
    app = App(Supplier(42))
    final_answer = app.resolve(int)
    assert final_answer == 42
