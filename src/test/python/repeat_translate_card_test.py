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

    def _get_text_printed_to_console(self) -> str:
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

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

        # when the first input is correct
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

        # when render the state after the first input is correct
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
            self._get_text_printed_to_console()
        )

        # when press Enter
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

    def test_second_input_is_correct(self) -> None:
        # given
        task_id = 223
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12])
        state = make_initial_state(self.cache, card, task)

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

        # when the first input is incorrect
        state = process_user_input(state, 'text3')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=0.0, note='text3'),
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='text3',
                user_translation='text3',
                correctness_indicator=False,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the sate after the first input is incorrect
        state.hist_rec = None
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

text3

{error}X{end}

""",
            self._get_text_printed_to_console()
        )

        # when the second input is correct
        state = process_user_input(state, 'text2')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='text3',
                user_translation='text2',
                correctness_indicator=True,
                correct_translation_entered=True,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state after the second input is correct
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
            self._get_text_printed_to_console()
        )

        # when press Enter
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
                first_user_translation='text3',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=True,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

    def test_show_answer_after_first_input_is_incorrect(self) -> None:
        # given
        task_id = 92
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12])
        state = make_initial_state(self.cache, card, task)

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

        # when the first input is incorrect
        state = process_user_input(state, 'text3')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=0.0, note='text3'),
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='text3',
                user_translation='text3',
                correctness_indicator=False,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state after the first input is incorrect
        state.hist_rec = None
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

text3

{error}X{end}

""",
            self._get_text_printed_to_console()
        )

        # when the "show answer" command is selected after the first incorrect input
        state = process_user_input(state, '`a')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=True,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='text3',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state showing the answer
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

{info}Translation:{end}

text2

{info}Transcription: {end}tran2

{prompt}(press Enter to hide the answer){end}

""",
            self._get_text_printed_to_console()
        )

        # when press Enter to hide the answer
        state = process_user_input(state, '')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='text3',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state after the answer is hidden
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

    def test_show_answer_before_first_input(self) -> None:
        # given
        task_id = 75
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12])
        state = make_initial_state(self.cache, card, task)

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

        # when the "show answer" command is selected before the first input
        state = process_user_input(state, '`a')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=True,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=0.0, note=''),
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state showing the answer
        state.hist_rec = None
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

{info}Translation:{end}

text2

{info}Transcription: {end}tran2

{prompt}(press Enter to hide the answer){end}

""",
            self._get_text_printed_to_console()
        )

        # when press Enter to hide the answer
        state = process_user_input(state, '')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state after the answer is hidden
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

    def test_user_enters_correct_translation_when_answer_is_showed(self) -> None:
        # given
        task_id = 462
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12])
        state = make_initial_state(self.cache, card, task)

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

""",
            self._get_text_printed_to_console()
        )

        # when the "show answer" command is selected before the first input
        state = process_user_input(state, '`a')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=True,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=0.0, note=''),
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state showing the answer
        state.hist_rec = None
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{prompt}Write translation to EN for:{end}

text1

{info}Translation:{end}

text2

{info}Transcription: {end}tran2

{prompt}(press Enter to hide the answer){end}

""",
            self._get_text_printed_to_console()
        )

        # when type the correct translation while the answer is still showing
        state = process_user_input(state, 'text2')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_12]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                dst=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                first_user_translation='',
                user_translation='text2',
                correctness_indicator=True,
                correct_translation_entered=True,
                enter_mark=False,
                err_msg=None,
            ),
            state
        )

        # when render the state after the answer is hidden and the correct translation is provided
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
            self._get_text_printed_to_console()
        )

    def test_for_readonly_user_enters_mark_0(self) -> None:
        # given
        task_id = 176
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_21])
        state = make_initial_state(self.cache, card, task)

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{prompt}Recall translation to PL for:{end}

text2

""",
            self._get_text_printed_to_console()
        )

        # when press Enter to show the correct answer
        state = process_user_input(state, '')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_21]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                src=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                dst=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                first_user_translation='',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=False,
                enter_mark=True,
                err_msg=None,
            ),
            state
        )

        # when render the state after the correct translation is shown
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{prompt}Recall translation to PL for:{end}

text2

{info}Translation:{end}

text1

{info}Transcription: {end}tran1

{prompt}Enter mark [1]: {end}""",
            self._get_text_printed_to_console()
        )

        # when type mark 0
        state = process_user_input(state, '0')

        # then
        self.assertEqual(
            TranslateTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.translate_21]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=0.0, note=''),
                task_continuation=TaskContinuation.NEXT_TASK,
                src=CardTranslateSide(lang_str='EN', read_only=0, text='text2', tran='tran2'),
                dst=CardTranslateSide(lang_str='PL', read_only=1, text='text1', tran='tran1'),
                first_user_translation='',
                user_translation=None,
                correctness_indicator=None,
                correct_translation_entered=True,
                enter_mark=True,
                err_msg=None,
            ),
            state
        )

    def test_for_readonly_user_presses_enter_for_mark_1(self) -> None:
        raise Exception('not implemented')

    def test_for_readonly_user_selects_a_command_before_revealing_the_answer(self) -> None:
        raise Exception('not implemented')

    def test_for_readonly_user_selects_a_command_instead_of_providing_a_mark(self) -> None:
        raise Exception('not implemented')