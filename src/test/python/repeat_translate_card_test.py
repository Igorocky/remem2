import sys

sys.path.append('../../main/python')

from remem.constants import TaskTypes
from remem.repeat import TaskContinuation

from remem.dtos import CardTranslate, Task

from remem.cache import Cache
from remem.repeat.repeat_translate_card import make_initial_state, TranslateTaskState, CardTranslateSide
from testutils import CacheMock

from unittest import TestCase


def make_simple_card() -> CardTranslate:
    return CardTranslate(
        lang1_id=0, read_only1=1, text1='text1', tran1='tran1',
        lang2_id=1, read_only2=0, text2='text2', tran2='tran2')


class MakeInitialStateTest(TestCase):
    def _init_mocks(self) -> None:
        self.cache: Cache = CacheMock()  # type: ignore[assignment]
        self.card = make_simple_card()

    def test_make_initial_state_dir12(self) -> None:
        # given
        self._init_mocks()
        task = Task(task_type_id=self.cache.task_types_si[TaskTypes.translate_12])

        # when
        state = make_initial_state(self.cache, self.card, task)

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation=None,
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

    def test_make_initial_state_dir21(self) -> None:
        # given
        self._init_mocks()
        task = Task(task_type_id=self.cache.task_types_si[TaskTypes.translate_21])

        # when
        state = make_initial_state(self.cache, self.card, task)

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(task_type_id=self.cache.task_types_si[TaskTypes.translate_21]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                dst=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                first_user_translation=None,
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )
