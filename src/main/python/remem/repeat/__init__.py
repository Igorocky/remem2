import math
import random
from dataclasses import dataclass, field
from enum import Enum

from remem.dtos import TaskWithBaseCard, TaskHistRec, Task


class TaskContinuation(Enum):
    EXIT = 1
    CONTINUE_TASK = 2
    NEXT_TASK = 3


@dataclass
class TaskWithHist:
    task: TaskWithBaseCard
    hist: list[TaskHistRec]
    last_repeated: int


@dataclass
class RepeatTaskState:
    task: Task = field(default_factory=lambda: Task())
    show_answer: bool = False
    edit_card: bool = False
    print_stats: bool = False
    task_continuation: TaskContinuation = TaskContinuation.CONTINUE_TASK


def select_random_tasks_from_beginning(
        sorted_tasks: list[TaskWithHist],
        max_num_of_tasks: int,
        preferred_folders: list[int]
) -> list[TaskWithHist]:
    if len(sorted_tasks) == 0:
        return []
    src = sorted_tasks.copy()
    dst: list[TaskWithHist] = []
    while len(dst) < max_num_of_tasks and len(src) > 0:
        time_span_for_search = math.fabs(src[0].last_repeated - src[-1].last_repeated) * 0.2
        for folder_id in preferred_folders:
            tasks_to_select_from = [
                t for t in src
                if (math.fabs(t.last_repeated - src[0].last_repeated) <= time_span_for_search
                    and t.task.card.folder_id == folder_id)]
            if len(tasks_to_select_from) > 0:
                selected_task = tasks_to_select_from[random.randint(0, len(tasks_to_select_from) - 1)]
                break
        else:
            tasks_to_select_from = [
                t for t in src
                if math.fabs(t.last_repeated - src[0].last_repeated) <= time_span_for_search]
            if len(tasks_to_select_from) > 0:
                selected_task = tasks_to_select_from[random.randint(0, len(tasks_to_select_from) - 1)]
            else:
                break
        dst.append(selected_task)
        src = [t for t in src if t.task.id != selected_task.task.id]
        preferred_folders.remove(selected_task.task.card.folder_id)
        preferred_folders.append(selected_task.task.card.folder_id)
    return dst
