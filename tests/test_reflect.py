from injectionkit import reflect


def test_function() -> None:
    def hello(name: str, age: int) -> str:
        return f"Hello, I'm {name}, {age} years old."

    function = reflect.injective_of(hello)
    assert function.parameters[0].annotation is str
    assert function.parameters[1].annotation is int
    assert function.returns is str


class Student(object):
    name: str
    age: int

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def hello(self) -> str:
        return f"Hello, I'm {self.name}, {self.age} years old."


def test_constructor() -> None:
    constructor = reflect.injective_of(Student)
    assert constructor.parameters[0].annotation is str
    assert constructor.parameters[1].annotation is int
    assert constructor.returns is Student

    invoker = constructor.invoker()
    invoker.argument(constructor.parameters[0], "Cylix")
    invoker.argument(constructor.parameters[1], 23)
    student = invoker.invoke()
    assert isinstance(student, Student)
    assert student.name == "Cylix"
    assert student.age == 23


def test_method() -> None:
    student = Student("Cylix", 23)
    method = reflect.injective_of(student.hello)
    assert method.parameters == []
    assert method.returns is str

    invoker = method.invoker()
    assert invoker.invoke() == "Hello, I'm Cylix, 23 years old."
