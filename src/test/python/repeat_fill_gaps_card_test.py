import dataclasses
import re
import sys

sys.path.append('../../main/python')

from remem.app_settings import AppSettings
from remem.console import Console

from remem.constants import TaskTypes
from remem.repeat import TaskContinuation

from remem.dtos import Task, CardFillGaps

from remem.cache import Cache
from remem.repeat.repeat_fill_gaps_card import make_initial_state, FillGapsTaskState
from testutils import CacheMock

from unittest import TestCase


def make_simple_card() -> CardFillGaps:
    return CardFillGaps(
        lang_id=1, text='part1 [[ hidden1 | hint1 | note1 ]] part2 [[ hidden2 | hint2 | note2 ]] part3',
        notes='common-notes')


_console = Console(AppSettings())
end = re.match(r'^.*some_text(.*)$', _console.mark_hint('some_text')).group(1)  # type: ignore[union-attr]
hint = re.match(r'^(.*)some_text.*$', _console.mark_hint('some_text')).group(1)  # type: ignore[union-attr]
error = re.match(r'^(.*)some_text.*$', _console.mark_error('some_text')).group(1)  # type: ignore[union-attr]
success = re.match(r'^(.*)some_text.*$', _console.mark_success('some_text')).group(1)  # type: ignore[union-attr]
info = re.match(r'^(.*)some_text.*$', _console.mark_info('some_text')).group(1)  # type: ignore[union-attr]
prompt = re.match(r'^(.*)some_text.*$', _console.mark_prompt('some_text')).group(1)  # type: ignore[union-attr]


class MakeInitialStateTest(TestCase):
    def _init_mocks(self) -> None:
        self.cache: Cache = CacheMock()  # type: ignore[assignment]
        self.card = make_simple_card()

    def test_make_initial_state_no_err(self) -> None:
        # given
        self._init_mocks()
        task = Task(task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps])

        # when
        state = make_initial_state(self.cache, self.card, task)

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                card=self.card,
                card_is_valid=True,
                text_parts=['part1', 'part2', 'part3'],
                answers=['hidden1', 'hidden2'],
                hints=['hint1', 'hint2'],
                notes=['note1', 'note2'],
                first_user_inputs=[None, None],
                user_input=None,
                correctness_indicator=None,
                correct_text_entered=[False, False],
                err_msg=None,
            ),
            state
        )

    def test_make_initial_state_with_err(self) -> None:
        # given
        self._init_mocks()
        task = Task(task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps])
        card = dataclasses.replace(self.card, text='part1 [[ hidden1 | hint1 | note1 part2')

        # when
        state = make_initial_state(self.cache, card, task)

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                card=card,
                card_is_valid=False,
            ),
            state
        )
