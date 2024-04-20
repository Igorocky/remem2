import re
import sys

sys.path.append('../../main/python')

from remem.app_settings import AppSettings
from remem.console import Console

from remem.constants import TaskTypes
from remem.repeat import TaskContinuation

from remem.dtos import CardTranslate, Task, TaskHistRec

from remem.cache import Cache
from remem.repeat.repeat_translate_card import make_initial_state, TranslateTaskState, CardTranslateSide, \
    render_state, process_user_input
from testutils import CacheMock, ConsoleMock

from unittest import TestCase


def make_simple_card() -> CardTranslate:
    return CardTranslate(
        lang1_id=0, read_only1=1, text1='text1', tran1='tran1',
        lang2_id=1, read_only2=0, text2='text2', tran2='tran2')


end = re.match(r'^.*some_text(.*)$', Console(AppSettings()).mark_hint('some_text')).group(1)  # type: ignore[union-attr]
hint = re.match(r'^(.*)some_text.*$', Console(AppSettings()).mark_hint('some_text')).group(
    1)  # type: ignore[union-attr]
error = re.match(r'^(.*)some_text.*$', Console(AppSettings()).mark_error('some_text')).group(
    1)  # type: ignore[union-attr]
success = re.match(r'^(.*)some_text.*$', Console(AppSettings()).mark_success('some_text')).group(
    1)  # type: ignore[union-attr]
info = re.match(r'^(.*)some_text.*$', Console(AppSettings()).mark_info('some_text')).group(
    1)  # type: ignore[union-attr]
prompt = re.match(r'^(.*)some_text.*$', Console(AppSettings()).mark_prompt('some_text')).group(
    1)  # type: ignore[union-attr]


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


class FlowTest(TestCase):
    def _init_mocks(self) -> None:
        self.cache: Cache = CacheMock()  # type: ignore[assignment]
        self.console: Console = ConsoleMock(AppSettings())  # type: ignore[assignment]

    def get_text_printed_to_console(self) -> str:
        text = self.console.text  # type: ignore[attr-defined]
        self.console.reset()  # type: ignore[attr-defined]
        return text  # type: ignore[no-any-return]

    def test_first_input_is_correct(self) -> None:
        # given
        task_id = 391
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12])
        state = make_initial_state(self.cache, card, task)

        # when
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self.get_text_printed_to_console()
        )

        # when
        state = process_user_input(state, 'text2')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=1.0, note=card.text2),
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation=card.text2,
                user_translation=card.text2,
                correctness_indicator=True,
                correct_translation_entered=True,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when
        state.hist_rec = None
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

text2

{success}V{end}

{info}Transcription: {end}tran2

{prompt}(press Enter to go to the next task){end}""",
            self.get_text_printed_to_console()
        )

        # when
        state = process_user_input(state, '')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.NEXT_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation=card.text2,
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=True,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )
