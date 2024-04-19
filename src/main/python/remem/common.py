import datetime
import math
import re
import time
from typing import TypeVar, Callable, Generic, Tuple
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
    match_res = re.match(r'^(\d+)([mhd])$', dur_str)
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
                raise Exception(f'Unexpected unit "{unit}"')
    else:
        raise Exception(f'Unexpected format of duration "{dur_str}"')


class DurationStrToSecondsTest(TestCase):
    def test_duration_str_to_seconds(self) -> None:
        self.assertEqual(duration_str_to_seconds('1m'), 60)
        self.assertEqual(duration_str_to_seconds('16m'), 16 * 60)
        self.assertEqual(duration_str_to_seconds('1h'), 60 * 60)
        self.assertEqual(duration_str_to_seconds('32h'), 32 * 60 * 60)
        self.assertEqual(duration_str_to_seconds('1d'), 60 * 60 * 24)
        self.assertEqual(duration_str_to_seconds('7d'), 7 * 60 * 60 * 24)


def seconds_to_duration_str(seconds: int) -> str:
    sign_str = '' if seconds >= 0 else '-'
    seconds = int(math.fabs(seconds))

    days = math.floor(seconds / _seconds_in_day)
    days_str = '' if days == 0 else str(days) + 'd'
    seconds = seconds - days * _seconds_in_day

    hours = math.floor(seconds / _seconds_in_hour)
    hours_str = '' if hours == 0 else str(hours) + 'h'
    if days > 0:
        return sign_str + days_str + hours_str
    seconds = seconds - hours * _seconds_in_hour

    minutes = math.floor(seconds / _seconds_in_minute)
    minutes_str = '' if minutes == 0 else str(minutes) + 'm'
    if hours > 0:
        return sign_str + hours_str + minutes_str
    seconds = math.ceil(seconds - minutes * _seconds_in_minute)

    seconds_str = '' if seconds == 0 and minutes > 0 else str(seconds) + 's'
    if minutes > 0:
        return sign_str + minutes_str + seconds_str
    return sign_str + seconds_str


class SecondsToDurationStrTest(TestCase):
    def test_seconds_to_duration_str(self) -> None:
        self.assertEqual(seconds_to_duration_str(0), '0s')
        self.assertEqual(seconds_to_duration_str(27), '27s')

        self.assertEqual(seconds_to_duration_str(duration_str_to_seconds('1m') + 8), '1m8s')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('8h') + duration_str_to_seconds('13m') + 49), '8h13m')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('17d')
                                    + duration_str_to_seconds('9h') + duration_str_to_seconds('25m') + 33), '17d9h')

        self.assertEqual(seconds_to_duration_str(duration_str_to_seconds('1m') + 0), '1m')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('8h') + duration_str_to_seconds('0m') + 0), '8h')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('17d')
                                    + duration_str_to_seconds('0h') + duration_str_to_seconds('0m') + 0), '17d')


def extract_gaps_from_text(text: str) -> Tuple[list[str], list[str], list[str], list[str]] | None:
    text = text.strip()
    if len(text) == 0:
        return None
    split = re.split(r'\[\[|\]\]', text)
    if len(split) == 1 or len(split) % 2 == 0:
        return None
    text_parts: list[str] = []
    answers: list[str] = []
    hints: list[str] = []
    notes: list[str] = []
    for i, part in enumerate(split):
        if i % 2 == 0:
            text_parts.append(part.strip())
        else:
            gap = part.split('|')
            answers.append(gap[0].strip())
            if len(gap) > 1:
                hints.append(gap[1].strip())
            else:
                hints.append('')
            if len(gap) > 2:
                notes.append(gap[2].strip())
            else:
                notes.append('')
    return text_parts, answers, hints, notes


class ExtractGapsFromTextTest(TestCase):
    def test_extract_gaps_from_text(self) -> None:
        self.assertEqual(None, extract_gaps_from_text('abc def ghi'))
        self.assertEqual(None, extract_gaps_from_text('abc [[def ghi'))
        self.assertEqual((['abc', 'ghi'], ['def'], [''], ['']), extract_gaps_from_text('abc [[def]] ghi'))
        self.assertEqual(
            (['abc', 'ghi', 'mno'], ['def', 'jkl'], ['', '123'], ['', '456']),
            extract_gaps_from_text('abc [[def]] ghi [[jkl|123|456]] mno')
        )
        self.assertEqual(
            (['abc', 'ghi', ''], ['def', 'jkl'], ['', '123'], ['', '456']),
            extract_gaps_from_text('abc [[def]] ghi [[jkl|123|456]]')
        )
        self.assertEqual(
            (['', 'ghi', 'mno'], ['def', 'jkl'], ['', '123'], ['', '456']),
            extract_gaps_from_text('[[def]] ghi [[jkl|123|456]] mno')
        )
