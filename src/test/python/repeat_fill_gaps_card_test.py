import dataclasses
import re
import sys

sys.path.append('../../main/python')

from remem.app_settings import AppSettings
from remem.console import Console, add_color

from remem.constants import TaskTypes
from remem.repeat import TaskContinuation

from remem.dtos import Task, CardFillGaps, TaskHistRec

from remem.cache import Cache
from remem.repeat.repeat_fill_gaps_card import make_initial_state, FillGapsTaskState, render_state, orange, \
    process_user_input
from testutils import CacheMock, ConsoleMock

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
_orange = re.match(r'^(.*)some_text.*$', add_color(orange, 'some_text')).group(1)  # type: ignore[union-attr]


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


class FlowTest(TestCase):
    def _init_mocks(self) -> None:
        self.cache: Cache = CacheMock()  # type: ignore[assignment]
        self.console: Console = ConsoleMock(AppSettings())  # type: ignore[assignment]

    def _get_text_printed_to_console(self) -> str:
        text = self.console.text  # type: ignore[attr-defined]
        self.console.reset()  # type: ignore[attr-defined]
        return text  # type: ignore[no-any-return]

    def test_first_input_is_correct_second_one_is_not_and_show_ans_after_second(self) -> None:
        # given
        task_id = 791
        self._init_mocks()
        card = make_simple_card()
        task = Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps])
        state = make_initial_state(self.cache, card, task)

        # when render the initial state
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{prompt}Fill the gap #1:{end}

part1 {_orange}#1{end} part2 {_orange}#2{end} part3

{info}Hint: {end}hint1

""",
            self._get_text_printed_to_console()
        )

        # when the first input is correct
        state = process_user_input(state, 'hidden1')

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                card=card,
                card_is_valid=True,
                text_parts=['part1', 'part2', 'part3'],
                answers=['hidden1', 'hidden2'],
                hints=['hint1', 'hint2'],
                notes=['note1', 'note2'],
                first_user_inputs=['hidden1', None],
                user_input=None,
                correctness_indicator=None,
                correct_text_entered=[True, False],
                err_msg=None,
            ),
            state
        )

        # when render the state after the first correct input
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{success}V{end} #1 hidden1
    note1

{prompt}Fill the gap #2:{end}

part1 hidden1 part2 {_orange}#2{end} part3

{info}Hint: {end}hint2

""",
            self._get_text_printed_to_console()
        )

        # when the second input is incorrect
        state = process_user_input(state, 'hidden3')

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                card=card,
                card_is_valid=True,
                text_parts=['part1', 'part2', 'part3'],
                answers=['hidden1', 'hidden2'],
                hints=['hint1', 'hint2'],
                notes=['note1', 'note2'],
                first_user_inputs=['hidden1', 'hidden3'],
                user_input='hidden3',
                correctness_indicator=False,
                correct_text_entered=[True, False],
                err_msg=None,
            ),
            state
        )

        # when render the state after the second incorrect input
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}a - show answer    e - exit    u - update card    s - show statistics{end}

{success}V{end} #1 hidden1
    note1

{prompt}Fill the gap #2:{end}

part1 hidden1 part2 {_orange}#2{end} part3

{info}Hint: {end}hint2

hidden3

{error}X{end}

""",
            self._get_text_printed_to_console()
        )

        # when the "show answer" command is selected
        state = process_user_input(state, '`a')

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=True,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.CONTINUE_TASK,
                card=card,
                card_is_valid=True,
                text_parts=['part1', 'part2', 'part3'],
                answers=['hidden1', 'hidden2'],
                hints=['hint1', 'hint2'],
                notes=['note1', 'note2'],
                first_user_inputs=['hidden1', 'hidden3'],
                user_input=None,
                correctness_indicator=None,
                correct_text_entered=[True, False],
                err_msg=None,
            ),
            state
        )

        # when render the state showing the answer
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{success}V{end} #1 hidden1
    note1

{prompt}Fill the gap #2:{end}

part1 hidden1 part2 {_orange}#2{end} part3

{info}Hint: {end}hint2

{info}The answer for the gap #2 is:{end}

hidden2

{info}Note: {end}note2

{prompt}(press Enter to hide the answer){end}

""",
            self._get_text_printed_to_console()
        )

        # when the second correct answer is entered
        state = process_user_input(state, 'hidden2')

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=TaskHistRec(task_id=task_id, mark=0.5, note='V exp: hidden1 & act: hidden1 | '
                                                                     'X exp: hidden2 & act: hidden3'),
                task_continuation=TaskContinuation.CONTINUE_TASK,
                card=card,
                card_is_valid=True,
                text_parts=['part1', 'part2', 'part3'],
                answers=['hidden1', 'hidden2'],
                hints=['hint1', 'hint2'],
                notes=['note1', 'note2'],
                first_user_inputs=['hidden1', 'hidden3'],
                user_input=None,
                correctness_indicator=None,
                correct_text_entered=[True, True],
                err_msg=None,
            ),
            state
        )

        # when render the state when all gaps are filled
        state.hist_rec = None
        render_state(self.console, state)

        # then
        self.assertEqual(
            f"""{hint}e - exit    u - update card    s - show statistics{end}

{success}V{end} #1 hidden1
    note1
{success}V{end} #2 hidden2
    note2

{info}Notes:{end}

common-notes

{info}All gaps are filled.{end}

part1 hidden1 part2 hidden2 part3

{prompt}(press Enter to go to the next task){end}""",
            self._get_text_printed_to_console()
        )

        # when press Enter to go to the next task
        state = process_user_input(state, '')

        # then
        self.assertEqual(
            FillGapsTaskState(
                task=Task(id=task_id, task_type_id=self.cache.task_types_si[TaskTypes.fill_gaps]),
                show_answer=False,
                edit_card=False,
                print_stats=False,
                hist_rec=None,
                task_continuation=TaskContinuation.NEXT_TASK,
                card=card,
                card_is_valid=True,
                text_parts=['part1', 'part2', 'part3'],
                answers=['hidden1', 'hidden2'],
                hints=['hint1', 'hint2'],
                notes=['note1', 'note2'],
                first_user_inputs=['hidden1', 'hidden3'],
                user_input=None,
                correctness_indicator=None,
                correct_text_entered=[True, True],
                err_msg=None,
            ),
            state
        )