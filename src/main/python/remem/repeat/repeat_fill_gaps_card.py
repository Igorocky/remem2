import dataclasses
from dataclasses import dataclass, field
from typing import Callable

from remem.app_context import AppCtx
from remem.common import extract_gaps_from_text
from remem.console import clear_screen, add_color
from remem.dao import select_card, insert_task_hist
from remem.data_commands import edit_card_by_id
from remem.dtos import Task, TaskHistRec, CardFillGaps
from remem.repeat import TaskContinuation

orange = (255, 109, 10)


@dataclass
class FillGapsTaskState:
    task: Task
    card: CardFillGaps
    card_is_valid: bool
    text_parts: list[str]
    answers: list[str]
    hints: list[str]
    notes: list[str]
    first_user_inputs: list[str | None] = field(default_factory=lambda: [])
    user_input: None | str = None
    correctness_indicator: bool | None = None
    correct_text_entered: list[bool] = field(default_factory=lambda: [])
    show_answer: bool = False
    edit_card: bool = False
    print_stats: bool = False
    err_msg: str | None = None
    task_continuation: TaskContinuation = TaskContinuation.CONTINUE_TASK


def make_initial_state(ctx: AppCtx, task: Task) -> FillGapsTaskState:
    card = select_card(ctx.database.con, ctx.cache, task.card_id)
    if not isinstance(card, CardFillGaps):
        raise Exception(f'CardFillGaps was expected but got {card}')
    gaps = extract_gaps_from_text(card.text)
    if gaps is None:
        return FillGapsTaskState(
            task=task,
            card=card,
            card_is_valid=False,
            text_parts=[],
            answers=[],
            hints=[],
            notes=[],
        )
    text_parts, answers, hints, notes = gaps
    return FillGapsTaskState(
        task=task,
        card=card,
        card_is_valid=True,
        text_parts=text_parts,
        answers=answers,
        hints=hints,
        notes=notes,
        first_user_inputs=[None for _ in range(len(gaps))],
        correct_text_entered=[False for _ in range(len(gaps))],
    )


def render_state(ctx: AppCtx, state: FillGapsTaskState) -> None:
    c = ctx.console

    if state.card_is_valid and not all(state.correct_text_entered):
        cur_gap_idx = state.correct_text_entered.index(False)
    else:
        cur_gap_idx = None

    def rnd_commands() -> None:
        show_answer_cmd_descr = 'a - show answer    ' if cur_gap_idx is not None else ''
        c.hint(f'{show_answer_cmd_descr}e - exit    u - update card    s - show statistics')

    def rnd_answers() -> None:
        max_idx = cur_gap_idx - 1 if cur_gap_idx is not None else len(state.answers)
        for i in range(max_idx + 1):
            status = c.mark_success('V')
            answer = state.answers[i]
            note = state.notes[i]
            print(f'{status} #{i + 1} {answer}')
            if note != '':
                print(f'    {note}')
        if cur_gap_idx is None and state.card.notes != '':
            print()
            print('Notes:')
            print(state.card.notes)

    def rnd_question() -> None:
        if cur_gap_idx is not None:
            c.prompt(f'Fill the gap #{cur_gap_idx + 1}:')
        else:
            c.info('All gaps are filled')
        text_arr = []
        for i, ans in enumerate(state.answers):
            text_arr.append(state.text_parts[i])
            if state.correct_text_entered[i]:
                text_arr.append(ans)
            else:
                text_arr.append(add_color(orange, f'# {i + 1}'))
        text_arr.append(state.text_parts[-1])
        print()
        print(' '.join(text_arr).strip())
        if cur_gap_idx is not None:
            hint = state.hints[cur_gap_idx]
            if hint != '':
                print()
                print(c.mark_info('Hint: ') + hint)

    def rnd_answer_for_curr_gap() -> None:
        if state.show_answer and cur_gap_idx is not None:
            c.info(f'The answer for the gap #{cur_gap_idx + 1} is:\n')
            print(state.answers[cur_gap_idx])
            note = state.notes[cur_gap_idx]
            if note != '':
                print()
                print(c.mark_info('Note: ') + note)

    def rnd_user_input() -> None:
        if state.user_input is not None:
            print(state.user_input)

    def rnd_indicator() -> None:
        match state.correctness_indicator:
            case True:
                c.success('V')
            case False:
                c.error('X')

    def rnd_err_msg() -> None:
        if not state.card_is_valid:
            c.error('The card is not correctly formatted.')
        if state.err_msg is not None:
            c.error(state.err_msg)

    def rnd_prompt() -> None:
        if cur_gap_idx is None:
            c.hint('(Press Enter to go to the next task)')
        elif state.show_answer:
            c.hint('(press Enter to hide the answer)')

    rnd_commands()
    if state.card_is_valid:
        print()
        rnd_answers()
        print()
        rnd_question()
        print()
        rnd_answer_for_curr_gap()
        print()
        rnd_user_input()
        print()
        rnd_indicator()
        print()
        rnd_err_msg()
    print()
    rnd_prompt()


def process_user_input(
        ctx: AppCtx,
        state: FillGapsTaskState,
        user_input: str
) -> FillGapsTaskState:
    def update_state(
            first_user_inputs: list[str | None] = state.first_user_inputs,
            user_input: None | str = None,
            correctness_indicator: bool | None = None,
            correct_text_entered: list[bool] = state.correct_text_entered,
            show_answer: bool = False,
            edit_card: bool = False,
            print_stats: bool = False,
            err_msg: str | None = None,
            task_continuation: TaskContinuation = TaskContinuation.CONTINUE_TASK,
    ) -> FillGapsTaskState:
        return dataclasses.replace(
            state,
            first_user_inputs=first_user_inputs,
            user_input=user_input,
            correctness_indicator=correctness_indicator,
            correct_text_entered=correct_text_entered,
            show_answer=show_answer,
            edit_card=edit_card,
            print_stats=print_stats,
            err_msg=err_msg,
            task_continuation=task_continuation,
        )

    if state.card_is_valid and not all(state.correct_text_entered):
        cur_gap_idx = state.correct_text_entered.index(False)
    else:
        cur_gap_idx = None

    def process_command(cmd: str) -> FillGapsTaskState:
        match cmd:
            case 'e':
                return update_state(task_continuation=TaskContinuation.EXIT)
            case 'a' if cur_gap_idx is not None:
                first_user_inputs = state.first_user_inputs.copy()
                first_user_inputs[cur_gap_idx] = ''
                return update_state(first_user_inputs=first_user_inputs, show_answer=True)
            case 'u':
                return update_state(edit_card=True)
            case 's':
                return update_state(print_stats=True)
            case _:
                return update_state(err_msg=f'Unknown command "{cmd}"')

    con = ctx.database.con
    if state.enter_mark:
        try:
            user_input = user_input.strip()
            if user_input.startswith('`'):
                return process_command(user_input[1:])
            mark = 1.0 if user_input == '' else float(user_input)
            if not (0.0 <= mark <= 1.0):
                return update_state(enter_mark=True, err_msg='The mark must be between 0.0 and 1.0 (inclusively)')
            insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=mark, note=''))
            return update_state(correct_translation_entered=True, enter_mark=False,
                                task_continuation=TaskContinuation.NEXT_TASK)
        except ValueError:
            return update_state()
    if user_input.startswith('`'):
        return process_command(user_input[1:])
    if state.correct_translation_entered:
        if user_input == '':
            return update_state(task_continuation=TaskContinuation.NEXT_TASK)
        else:
            return update_state()
    if state.dst.read_only:
        if state.first_user_translation is None:
            return update_state(first_user_translation='', enter_mark=True)
        else:
            return update_state()
    elif user_input != state.dst.text:
        if state.first_user_translation is None:
            insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=0.0, note=user_input))
            return update_state(first_user_translation=user_input, correctness_indicator=False)
        return update_state(correctness_indicator=False if user_input != '' else None)
    else:
        if state.first_user_translation is None:
            insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=1.0, note=user_input))
            return update_state(first_user_translation=user_input, correctness_indicator=True,
                                correct_translation_entered=True)
        return update_state(correctness_indicator=True, correct_translation_entered=True)


def repeat_translate_task(ctx: AppCtx, task: Task, print_stats: Callable[[], None]) -> TaskContinuation:
    state = make_initial_state(ctx, task)
    while True:
        clear_screen()
        render_state(ctx, state)
        state = process_user_input(ctx, state, input())
        match state.task_continuation:
            case TaskContinuation.CONTINUE_TASK:
                if state.edit_card:
                    state.edit_card = False
                    edit_card_by_id(ctx, state.task.card_id)
                if state.print_stats:
                    state.print_stats = False
                    print_stats()
            case act:
                return act
