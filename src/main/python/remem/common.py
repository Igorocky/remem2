import datetime
import math
import numbers
import re
import time
from sqlite3 import Connection
from typing import TypeVar, Callable, Generic, Tuple, Any
from unittest import TestCase

from remem.console import select_multiple_options, select_single_option, Console
from remem.dtos import FolderWithPathDto

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
            answer = gap[0].strip()
            if answer == '':
                return None
            answers.append(answer)
            hints.append(gap[1].strip() if len(gap) > 1 else '')
            notes.append(gap[2].strip() if len(gap) > 2 else '')
    return text_parts, answers, hints, notes


def first_defined(*args: Any) -> Any:
    for arg in args:
        if arg is not None:
            return arg
    return None


def print_table(header: list[str], data: list[list[Any]]) -> str:
    if len(data) == 0:
        return '-----------\nEmpty table\n-----------'
    col_width = [len(h) for h in header]
    col_is_number = [True for _ in header]
    for r in data:
        for i in range(len(r)):
            col_is_number[i] = col_is_number[i] and (r[i] is None or isinstance(r[i], numbers.Number))
            r[i] = str(r[i])
            col_width[i] = max(col_width[i], len(r[i]))
    header_str = ' '.join(
        h.rjust(col_width[i]) if col_is_number[i] else h.ljust(col_width[i]) for i, h in enumerate(header)
    )
    delim = '-' * len(header_str)
    res = [delim, header_str, delim]
    for row in data:
        res.append(' '.join(
            c.rjust(col_width[i]) if col_is_number[i] else c.ljust(col_width[i]) for i, c in enumerate(row)
        ))
    res.append(delim)
    return '\n'.join(res)


def print_table_from_dicts(data: list[dict[str, Any]]) -> str:
    if len(data) == 0:
        return '-----------\nEmpty table\n-----------'
    header = list(data[0].keys())
    return print_table(
        header=header,
        data=[[d[h] if h in d else None for h in header] for d in data]
    )


class PrintTableFromDictsTest(TestCase):
    def test_print_table_from_dicts(self) -> None:
        self.assertEqual(
            """------------------
    id name desc  
------------------
     1 AA   10    
  None BB   ..    
300000 CC   300000
------------------""",
            print_table_from_dicts([
                {'id': 1, 'name': 'AA', 'desc': 10},
                {'id': None, 'name': 'BB', 'desc': '..'},
                {'id': 300000, 'name': 'CC', 'desc': 300000},
            ])
        )


def enable_foreign_keys(con: Connection) -> None:
    con.execute('pragma foreign_keys = ON')
    if values(con.execute('pragma foreign_keys').fetchone())[0] != 1:
        raise Exception('Could not set foreign_keys = ON.')


def select_folders(c: Console, con: Connection, prompt: str, single: bool = False) -> list[FolderWithPathDto] | None:
    all_folders = [FolderWithPathDto(**r) for r in con.execute("""
        with recursive folders(id, path) as (
            select id, '/'||name from FOLDER where parent_id is null
            union all
            select ch.id, pr.path||'/'||ch.name
            from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            order by 1 desc
        )
        select id, path from folders
        order by path
    """)]
    folder_name_pat = input(prompt).lower().strip()
    matching_folders = [f for f in all_folders if folder_name_pat in f.path.lower()]
    if len(matching_folders) == 0:
        return None
    if single:
        idx = select_single_option(c, [f.path for f in matching_folders])
        if idx is None:
            return []
        idxs = [idx]
    else:
        idxs = select_multiple_options(c, [f.path for f in matching_folders])
    return [matching_folders[i] for i in idxs]
