from enum import Enum


class TaskContinuation(Enum):
    CANCEL = 1
    CONTINUE_TASK = 2
    NEXT_TASK = 3