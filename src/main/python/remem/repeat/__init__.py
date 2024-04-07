from remem.app_context import AppCtx
from remem.constants import TaskTypes
from remem.dtos import Task
from remem.repeat.repeat_translate_card import repeat_translate_task


def repeat_task(ctx: AppCtx, task: Task) -> None:
    match ctx.cache.task_types_is[task.task_type_id]:
        case TaskTypes.translate_12:
            repeat_translate_task(ctx, task)
        case TaskTypes.translate_21:
            repeat_translate_task(ctx, task)
        case _:
            raise Exception(f'Unexpected type of task: {task}')
