from enum import Enum


class TaskContinuation(Enum):
    EXIT = 1
    CONTINUE_TASK = 2
    NEXT_TASK = 3