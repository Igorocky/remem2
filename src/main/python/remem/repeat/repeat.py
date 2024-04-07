from unittest import TestCase

from remem.app_context import AppCtx
from remem.constants import TaskTypes
from remem.dao import select_tasks_by_ids, select_task_hist
from remem.dtos import Task, TaskHistRec
from remem.repeat.repeat_translate_card import repeat_translate_task


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
    def test_get_bucket_number(self):
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


def repeat_tasks(ctx: AppCtx, task_ids: list[int]) -> None:
    db = ctx.database
    tasks = select_tasks_by_ids(db.con, task_ids)
    hist = select_task_hist(db.con, task_ids, max_num_of_records_per_task=5)



def repeat_task(ctx: AppCtx, task: Task) -> None:
    match ctx.cache.task_types_is[task.task_type_id]:
        case TaskTypes.translate_12:
            repeat_translate_task(ctx, task)
        case TaskTypes.translate_21:
            repeat_translate_task(ctx, task)
        case _:
            raise Exception(f'Unexpected type of task: {task}')
