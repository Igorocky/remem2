from remem.cache import Cache
from remem.console import Console
from remem.constants import TaskTypes
from remem.dao import load_task
from remem.database import Database
from remem.dtos import Task


def repeat_translate_card(c: Console, db: Database, cache: Cache, task: Task):
    pass


def repeat_task(c: Console, db: Database, cache: Cache, task_id: int) -> None:
    task = load_task(db, cache, task_id)
    match task.task_type_code:
        case TaskTypes.translate_12:
            repeat_translate_card(c, db, cache, task_id, task)
