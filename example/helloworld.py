from dataclasses import dataclass

from injectionkit import App, Consumer, Provider
from injectionkit.option import Supplier


@dataclass(frozen=True)
class StudentParams(object):
    name: str
    age: int


class Student(object):
    name: str
    age: int

    def __init__(self, params: StudentParams) -> None:
        self.name = params.name
        self.age = params.age


@dataclass(frozen=True)
class TeacherParams(object):
    name: str


class Teacher(object):
    name: str
    student: Student

    def __init__(self, params: TeacherParams, student: Student) -> None:
        self.name = params.name
        self.student = student

    def teach(self) -> None:
        print(f"{self.name} is teaching {self.student.name}")


def teach(teacher: Teacher) -> None:
    teacher.teach()


def main() -> None:
    App(
        Supplier(StudentParams("Cylix", 23)),
        Supplier(TeacherParams("Ms. Lee")),
        Provider(Student),
        Provider(Teacher),
        Consumer(teach),
    ).run()


if __name__ == "__main__":
    main()
