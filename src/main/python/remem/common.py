import datetime
import re
import time
from typing import TypeVar, Callable, Generic
from unittest import TestCase

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


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


def fit_to_range(value: int, min_: int, max_: int) -> int:
    return min(max(value, min_), max_)


def values(d: dict[K, V]) -> list[V]:
    return list(d.values())


def unix_epoch_sec_now() -> int:
    now = datetime.datetime.now()
    return int(time.mktime(now.timetuple()))


def unix_epoch_sec_to_str(unix_epoch_sec: int) -> str:
    return str(datetime.datetime.fromtimestamp(unix_epoch_sec))


_seconds_in_minute = 60
_minutes_in_hour = 60
_hours_in_day = 24
_seconds_in_hour = _seconds_in_minute * _minutes_in_hour
_seconds_in_day = _seconds_in_hour * _hours_in_day


def duration_str_to_seconds(dur_str: str) -> int:
    match_res = re.match(r'^(\d)([mhd])$', dur_str)
    if match_res:
        val = int(match_res.group(1))
        unit = match_res.group(2)
        match unit:
            case 'm':
                return val * _seconds_in_minute
            case 'h':
                return val * _seconds_in_hour
            case 'd':
                return val * _seconds_in_day
            case _:
                raise Exception()


class DurationStrToSecondsTest(TestCase):
    def test_duration_str_to_seconds(self):
        self.assertEqual(duration_str_to_seconds('1m'), 60)
        self.assertEqual(duration_str_to_seconds('16m'), 16*60)
        self.assertEqual(duration_str_to_seconds('1h'), 60*60)
        self.assertEqual(duration_str_to_seconds('32h'), 32*60*60)
        self.assertEqual(duration_str_to_seconds('1d'), 60*60*24)
        self.assertEqual(duration_str_to_seconds('7d'), 7*60*60*24)
