from typing import TypeVar, Callable, Generic

T = TypeVar('T')


class Try(Generic[T]):
    def __init__(self, value: T | None = None, ex: Exception | None = None, func: Callable[[], T] | None = None):
        self.value: T | None
        if value is not None:
            self.value = value
            self.ex = None
        if ex is not None:
            self.value = None
            self.ex = ex
        if func is not None:
            try:
                self.value = func()
                self.ex = None
            except Exception as ex:
                self.value = None
                self.ex = ex

    def is_success(self) -> bool:
        return self.ex is None

    def is_failure(self) -> bool:
        return self.ex is not None


def try_(func: Callable[[], T]) -> Try[T]:
    return Try(func=func)
