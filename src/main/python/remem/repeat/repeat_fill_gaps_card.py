import dataclasses
from dataclasses import dataclass, field
from typing import Callable

from remem.app_context import AppCtx
from remem.common import extract_gaps_from_text
from remem.console import clear_screen
from remem.dao import select_card, insert_task_hist
from remem.data_commands import edit_card_by_id
from remem.dtos import Task, TaskHistRec, CardFillGaps
from remem.repeat import TaskContinuation


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
    con = ctx.database.con
    cache = ctx.cache
    card = select_card(con, cache, task.card_id)
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

    def rnd_commands() -> None:
        c.hint(f'a - show answer    e - exit    u - update card    s - show statistics\n')

    def rnd_question() -> None:
        if not all(state.correct_text_entered):
            c.prompt(f'Fill the gap #{state.correct_text_entered.index(False) + 1}:')
        else:
            c.info('All gaps are filled')
        text_arr = []
        for i, ans in enumerate(state.answers):
            text_arr.append(state.text_parts[i])
            if state.correct_text_entered[i]:
                text_arr.append(ans)
            else:
                text_arr.append('#' + str(i + 1))
        text_arr.append(state.text_parts[-1])
        print()
        print(' '.join(text_arr))
        print()
        if False in state.correct_text_entered:
            gap_idx = state.correct_text_entered.index(False)
            hint = state.hints[gap_idx]
            if hint != '':
                print(c.mark_info('Hint: ') + hint)
                print()

    def rnd_answer() -> None:
        if state.show_answer and not all(state.correct_text_entered):
            gap_idx = state.correct_text_entered.index(False)
            gap_num = gap_idx + 1
            c.info(f'The answer for the gap #{gap_num} is:\n')
            print(state.answers[gap_idx])
            print(state.notes[gap_idx] + '\n')

    def rnd_user_translation() -> None:
        if state.user_input is not None:
            print(state.user_input)

    def rnd_indicator() -> None:
        match state.correctness_indicator:
            case True:
                print(c.mark_success('V') + '\n')
            case False:
                print(c.mark_error('X') + '\n')

    def rnd_err_msg() -> None:
        if state.err_msg is not None:
            c.error(state.err_msg + '\n')

    def rnd_prompt() -> None:
        if state.enter_mark:
            print(c.mark_prompt('Enter mark [1]: '), end='')
        elif state.correct_translation_entered:
            print(c.mark_hint('(Press Enter to go to the next task)\n'))
        elif state.show_answer:
            print(c.mark_hint('(press Enter to hide the answer)\n'))

    rnd_commands()
    rnd_question()
    rnd_answer()
    rnd_user_translation()
    rnd_indicator()
    rnd_err_msg()
    rnd_prompt()


def process_user_input(
        ctx: AppCtx,
        state: TranslateTaskState,
        user_input: str
) -> TranslateTaskState:
    def update_state(
            first_user_translation: None | str = None,
            user_translation: None | str = None,
            correctness_indicator: bool | None = None,
            correct_translation_entered: bool = False,
            enter_mark: bool = False,
            show_answer: bool = False,
            edit_card: bool = False,
            print_stats: bool = False,
            err_msg: str | None = None,
            task_continuation: TaskContinuation = TaskContinuation.CONTINUE_TASK,
    ) -> TranslateTaskState:
        return dataclasses.replace(
            state,
            first_user_translation=state.first_user_translation if first_user_translation is None else first_user_translation,
            user_translation=user_translation,
            correctness_indicator=correctness_indicator,
            correct_translation_entered=state.correct_translation_entered or correct_translation_entered,
            enter_mark=state.enter_mark or enter_mark,
            show_answer=show_answer,
            edit_card=edit_card,
            print_stats=print_stats,
            err_msg=err_msg,
            task_continuation=task_continuation
        )

    def process_command(cmd: str) -> TranslateTaskState:
        match cmd:
            case 'e':
                return update_state(task_continuation=TaskContinuation.EXIT)
            case 'a' if not state.dst.read_only:
                if state.first_user_translation is None:
                    insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=0.0, note=''))
                    return update_state(first_user_translation='', show_answer=True)
                else:
                    return update_state(show_answer=True)
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
