import random
import re
from dataclasses import dataclass
from typing import Callable
from unittest import TestCase

from remem.app_context import AppCtx
from remem.commands import CollectionOfCommands
from remem.console import clear_screen
from remem.constants import TaskTypes
from remem.dao import select_tasks_by_ids, select_task_hist
from remem.dtos import Task, TaskHistRec
from remem.repeat import TaskContinuation
from remem.repeat.repeat_translate_card import repeat_translate_task


@dataclass
class TaskWithHist:
    task: Task
    hist: list[TaskHistRec]
    last_repeated: int


def select_random_tasks_from_beginning(sorted_tasks: list[TaskWithHist], num_of_tasks: int) -> list[TaskWithHist]:
    src = sorted_tasks.copy()
    num_of_tasks = min(num_of_tasks, len(sorted_tasks))
    dst: list[TaskWithHist] = []
    while len(dst) < num_of_tasks:
        idx = random.randint(0, min(5, len(src) - 1))
        dst.append(src.pop(idx))
    return dst


def get_bucket_number(hist: list[TaskHistRec], max_num: int = 5) -> int:
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
    num_of_buckets = 4
    buckets: list[list[TaskWithHist]] = [[] for _ in range(0, num_of_buckets)]
    for t in tasks:
        buckets[get_bucket_number(t.hist, max_num=num_of_buckets - 1)].append(t)
    return buckets


def select_tasks_to_repeat(buckets: list[list[TaskWithHist]]) -> list[TaskWithHist]:
    buckets_len = len(buckets)
    res: list[TaskWithHist] = []
    for i, b in enumerate(buckets):
        b.sort(key=lambda t: t.last_repeated)
        if i == 0:
            b.reverse()
        res = (res +
               select_random_tasks_from_beginning(
                   b,
                   num_of_tasks=buckets_len - i if i < buckets_len - 1 else int((1 + buckets_len) * buckets_len / 2)
               ))

    return res


def print_stats(ctx: AppCtx, buckets: list[list[TaskWithHist]]) -> None:
    ctx.console.info('Bucket counts:\n')
    for i, b in enumerate(buckets):
        print(f'{i} - {len(b)}')


def repeat_tasks(ctx: AppCtx, task_ids: list[int]) -> None:
    def load_tasks_to_repeat() -> list[TaskWithHist]:
        buckets = load_buckets(ctx, task_ids)
        clear_screen()
        print_stats(ctx, buckets)
        ctx.console.input('\nPress Enter')
        return select_tasks_to_repeat(buckets)

    tasks = load_tasks_to_repeat()
    act = TaskContinuation.NEXT_TASK
    while act != TaskContinuation.EXIT:
        if len(tasks) == 0:
            tasks = load_tasks_to_repeat()
        act = repeat_task(ctx, tasks.pop(0).task)


def repeat_task(ctx: AppCtx, task: Task) -> TaskContinuation:
    match ctx.cache.task_types_is[task.task_type_id]:
        case TaskTypes.translate_12:
            return repeat_translate_task(ctx, task)
        case TaskTypes.translate_21:
            return repeat_translate_task(ctx, task)
        case _:
            raise Exception(f'Unexpected type of task: {task}')


def cmd_repeat_tasks_by_ids(ctx: AppCtx) -> None:
    inp = ctx.console.input('Space separated list of tasks to repeat: ')
    task_ids = [int(m.group(1)) for m in re.finditer(r'(\S+)', inp)]
    repeat_tasks(ctx, task_ids)


def add_repeat_commands(ctx: AppCtx, commands: CollectionOfCommands) -> None:
    def add_command(cat: str, name: str, cmd: Callable[[AppCtx], None]) -> None:
        commands.add_command(cat, name, lambda: cmd(ctx))

    add_command('Repeat', 'repeat tasks by ids', cmd_repeat_tasks_by_ids)
