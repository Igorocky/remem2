import sys

sys.path.append('../../main/python')

from remem.constants import TaskTypes
from remem.repeat import TaskContinuation

from remem.dtos import CardTranslate, Task

from remem.cache import Cache
from remem.repeat.repeat_translate_card import make_initial_state, TranslateTaskState, CardTranslateSide
from testutils import CacheMock

from unittest import TestCase


class ProcessUserInputTest(TestCase):
    def test_make_initial_state_dir12(self) -> None:
        # given
        cache: Cache = CacheMock()  # type: ignore[assignment]
        card = CardTranslate(
            lang1_id=0, read_only1=0, text1='text1', tran1='tran1',
            lang2_id=1, read_only2=1, text2='text2', tran2='tran2')
        task = Task(task_type_id=cache.task_types_si[TaskTypes.translate_12])

        # when
        state = make_initial_state(cache, card, task)

        self.assertEqual(
            TranslateTaskState(
                task=Task(task_type_id=cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=0, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=1, text='text2', tran='tran2'),
                first_user_translation=None,
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )
