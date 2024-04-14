import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar
from unittest import TestCase

from remem.app_context import AppCtx
from remem.commands import CollectionOfCommands
from remem.console import select_single_option
from remem.constants import TaskTypes
from remem.dao import select_tasks_by_ids, select_task_hist
from remem.dtos import Task, TaskHistRec
from remem.repeat import TaskContinuation
from remem.repeat.repeat_translate_card import repeat_translate_task, ask_to_press_enter


@dataclass
class TaskWithHist:
    task: Task
    hist: list[TaskHistRec]
    last_repeated: int


T = TypeVar('T')


def select_random_elems_from_beginning(sorted_list: list[T], num_of_elems: int) -> list[T]:
    if len(sorted_list) == 0:
        return []
    src = sorted_list.copy()
    num_of_elems = min(num_of_elems, len(sorted_list))
    dst: list[T] = []
    while len(dst) < num_of_elems:
        if len(src) >= 20:
            max_idx = 6
        elif len(src) >= 15:
            max_idx = 5
        elif len(src) >= 10:
            max_idx = 4
        elif len(src) >= 5:
            max_idx = 3
        else:
            max_idx = min(1, len(src) - 1)
        idx = random.randint(0, max_idx)
        dst.append(src.pop(idx))
    return dst


_bucket_delay_minutes = [2, 5, 15, 30]
_num_of_buckets = len(_bucket_delay_minutes)


def get_bucket_number(hist: list[TaskHistRec], max_num: int = _num_of_buckets - 1) -> int:
    res = 0
    for i, r in enumerate(hist):
        if res >= max_num:
            break
        if r.mark >= 1.0:
            res = res + 1
        else:
            break
    return res


class GetBucketNumberTest(TestCase):
    def test_get_bucket_number(self) -> None:
        def make_hist(marks: list[float]) -> list[TaskHistRec]:
            return [TaskHistRec(mark=mark) for mark in marks]

        self.assertEqual(get_bucket_number([]), 0)
        self.assertEqual(get_bucket_number(make_hist([0.0])), 0)
        self.assertEqual(get_bucket_number(make_hist([1.0])), 1)
        self.assertEqual(get_bucket_number(make_hist([1.0, 0.0])), 1)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0])), 2)
        self.assertEqual(get_bucket_number(make_hist([0.0, 1.0])), 0)
        self.assertEqual(get_bucket_number(make_hist([1.0, 0.0, 1.0])), 1)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 1.0])), 3)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 0.0])), 2)
        self.assertEqual(get_bucket_number(make_hist([0.0, 1.0, 1.0, 1.0])), 0)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 1.0, 1.0])), 4)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 1.0, 1.0]), max_num=3), 3)


def load_buckets(ctx: AppCtx, task_ids: list[int]) -> list[list[TaskWithHist]]:
    def none_to_zero(i: int | None) -> int:
        return 0 if i is None else i

    db = ctx.database
    hist = select_task_hist(db.con, task_ids, max_num_of_records_per_task=5)
    tasks = [TaskWithHist(
        task=t,
        hist=hist[t.id] if t.id in hist else [],
        last_repeated=none_to_zero(hist[t.id][0].time) if t.id in hist else 0
    ) for t in select_tasks_by_ids(db.con, task_ids)]
    buckets: list[list[TaskWithHist]] = [[] for _ in range(0, _num_of_buckets)]
    for t in tasks:
        buckets[get_bucket_number(t.hist)].append(t)
    return buckets


def select_tasks_to_repeat(buckets: list[list[TaskWithHist]]) -> list[TaskWithHist]:
    buckets_len = len(buckets)
    res: list[TaskWithHist] = []
    for i, b in enumerate(buckets):
        min_delay_sec = _bucket_delay_minutes[i] * 60
        curr_time_sec = int(time.time())
        b = [t for t in b if curr_time_sec - t.last_repeated > min_delay_sec]
        b.sort(key=lambda t: t.last_repeated)
        if i == 0:
            b.reverse()
        res = res + select_random_elems_from_beginning(b, num_of_elems=buckets_len - i)
    res.sort(key=lambda t: t.last_repeated)
    idx = 1
    while len(res) == 0:
        bucket = buckets[-idx]
        bucket.sort(key=lambda t: t.last_repeated)
        if idx == len(buckets):
            bucket.reverse()
        res = select_random_elems_from_beginning(bucket, num_of_elems=1)
        idx = idx + 1
    return res


def print_stats(ctx: AppCtx, task_ids: list[int]) -> None:
    buckets = load_buckets(ctx, task_ids)
    ctx.console.info('\nBucket counts:\n')
    for i, b in enumerate(buckets):
        print(f'{i} - {len(b)}')
    ask_to_press_enter(ctx.console)


def repeat_tasks(ctx: AppCtx, task_ids: list[int]) -> None:
    def get_next_tasks_to_repeat() -> list[TaskWithHist]:
        return select_tasks_to_repeat(load_buckets(ctx, task_ids))

    tasks = get_next_tasks_to_repeat()
    act = TaskContinuation.NEXT_TASK
    while act != TaskContinuation.EXIT:
        if len(tasks) == 0:
            tasks = get_next_tasks_to_repeat()
        act = repeat_task(ctx, tasks.pop(0).task, print_stats=lambda: print_stats(ctx, task_ids))


def repeat_task(ctx: AppCtx, task: Task, print_stats: Callable[[], None]) -> TaskContinuation:
    match ctx.cache.task_types_is[task.task_type_id]:
        case TaskTypes.translate_12:
            return repeat_translate_task(ctx, task, print_stats)
        case TaskTypes.translate_21:
            return repeat_translate_task(ctx, task, print_stats)
        case _:
            raise Exception(f'Unexpected type of task: {task}')


def cmd_repeat_tasks(ctx: AppCtx) -> None:
    c = ctx.console
    db = ctx.database
    cache = ctx.cache
    folder_id = int(c.input('Folder id: ').strip())
    available_task_types = [cache.task_types_is[r['task_type_id']] for r in db.con.execute(
        """
            with recursive folders(id) as (
                select id from FOLDER where id = ?
                union all
                select ch.id
                from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            )
            select distinct t.task_type_id
            from folders f
                inner join CARD c on f.id = c.folder_id
                inner join TASK t on c.id = t.card_id
        """,
        [folder_id]
    )]
    if len(available_task_types) == 0:
        c.error('No tasks found in the specified folder')
        return
    available_task_types.sort()
    c.prompt('Select task type:')
    task_type_idx = select_single_option(available_task_types)
    if task_type_idx is None:
        return
    task_type_id = cache.task_types_si[available_task_types[task_type_idx]]
    task_ids = [r['id'] for r in db.con.execute(
        """
            with recursive folders(id) as (
                select id from FOLDER where id = :folder_id
                union all
                select ch.id
                from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            )
            select t.id
            from folders f
                inner join CARD c on f.id = c.folder_id
                inner join TASK t on c.id = t.card_id
            where t.task_type_id = :task_type_id
        """,
        dict(folder_id=folder_id, task_type_id=task_type_id)
    )]
    repeat_tasks(ctx, task_ids)


def add_repeat_commands(ctx: AppCtx, commands: CollectionOfCommands) -> None:
    def add_command(cat: str, name: str, cmd: Callable[[AppCtx], None]) -> None:
        commands.add_command(cat, name, lambda: cmd(ctx))

    add_command('Repeat', 'repeat tasks', cmd_repeat_tasks)
