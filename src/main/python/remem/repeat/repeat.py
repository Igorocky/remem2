from dataclasses import dataclass
from enum import Enum
from unittest import TestCase

from remem.app_context import AppCtx
from remem.constants import TaskTypes
from remem.dao import select_tasks_by_ids, select_task_hist
from remem.dtos import Task, TaskHistRec
from remem.repeat.repeat_translate_card import repeat_translate_task


class TaskContinuation(Enum):
    EXIT = 1
    CONTINUE_TASK = 2
    NEXT_TASK = 3


@dataclass
class TaskWithHist:
    task: Task
    hist: list[TaskHistRec]
    last_repeated: int


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
    buckets: list[list[TaskWithHist]] = [[]] * num_of_buckets
    for t in tasks:
        buckets[get_bucket_number(t.hist, max_num=num_of_buckets - 1)].append(t)
    return buckets


def select_tasks_to_repeat(buckets: list[list[TaskWithHist]]) -> list[TaskWithHist]:
    res: list[TaskWithHist] = []
    for i, b in enumerate(buckets):
        b.sort(key=lambda t: t.last_repeated)
        if i == 0:
            b.reverse()
        res = res + b[0:len(buckets) - i]

    return res


def repeat_tasks(ctx: AppCtx, task_ids: list[int]) -> None:
    pass


def repeat_task(ctx: AppCtx, task: Task) -> TaskContinuation:
    match ctx.cache.task_types_is[task.task_type_id]:
        case TaskTypes.translate_12:
            return repeat_translate_task(ctx, task)
        case TaskTypes.translate_21:
            return repeat_translate_task(ctx, task)
        case _:
            raise Exception(f'Unexpected type of task: {task}')
