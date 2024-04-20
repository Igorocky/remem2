import dataclasses
from dataclasses import dataclass, field

from remem.cache import Cache
from remem.common import extract_gaps_from_text, first_defined
from remem.console import add_color, Console
from remem.dtos import Task, TaskHistRec, CardFillGaps, AnyCard
from remem.repeat import TaskContinuation, RepeatTaskState

orange = (255, 109, 10)


@dataclass
class FillGapsTaskState(RepeatTaskState):
    card: CardFillGaps = field(default_factory=lambda: CardFillGaps())
    card_is_valid: bool = False
    text_parts: list[str] = field(default_factory=lambda: [])
    answers: list[str] = field(default_factory=lambda: [])
    hints: list[str] = field(default_factory=lambda: [])
    notes: list[str] = field(default_factory=lambda: [])
    first_user_inputs: list[str | None] = field(default_factory=lambda: [])
    user_input: None | str = None
    correctness_indicator: bool | None = None
    correct_text_entered: list[bool] = field(default_factory=lambda: [])
    err_msg: str | None = None


def make_initial_state(cache: Cache, card: AnyCard, task: Task) -> FillGapsTaskState:
    if not isinstance(card, CardFillGaps):
        raise Exception(f'CardFillGaps was expected but got {card}')
    gaps = extract_gaps_from_text(card.text)
    if gaps is None:
        return FillGapsTaskState(
            task=task,
            card=card,
            card_is_valid=False,
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
        first_user_inputs=[None for _ in range(len(answers))],
        correct_text_entered=[False for _ in range(len(answers))],
    )


def render_state(c: Console, state: FillGapsTaskState) -> None:
    if state.card_is_valid and not all(state.correct_text_entered):
        cur_gap_idx = state.correct_text_entered.index(False)
    else:
        cur_gap_idx = None

    # commands
    show_answer_cmd_descr = 'a - show answer    ' if cur_gap_idx is not None else ''
    c.hint(f'{show_answer_cmd_descr}e - exit    u - update card    s - show statistics')
    c.print()

    if not state.card_is_valid:
        c.error('The card is not correctly formatted.')
        c.print()
        return

    # answers
    for i in range(cur_gap_idx if cur_gap_idx is not None else len(state.answers)):
        status = c.mark_success('V')
        answer = state.answers[i]
        note = state.notes[i]
        c.print(f'{status} #{i + 1} {answer}')
        if note != '':
            c.print(f'    {note}')
    if cur_gap_idx is None or cur_gap_idx > 0:
        c.print()
    if cur_gap_idx is None and state.card.notes != '':
        c.info('Notes:')
        c.print()
        c.print(state.card.notes)
        c.print()

    # question
    if cur_gap_idx is not None:
        c.prompt(f'Fill the gap #{cur_gap_idx + 1}:')
    else:
        c.info('All gaps are filled.')
    c.print()
    text_arr = []
    for i, ans in enumerate(state.answers):
        text_arr.append(state.text_parts[i])
        if state.correct_text_entered[i]:
            text_arr.append(ans)
        else:
            text_arr.append(add_color(orange, f'#{i + 1}'))
    text_arr.append(state.text_parts[-1])
    c.print(' '.join(text_arr).strip())
    c.print()
    if cur_gap_idx is not None:
        hint = state.hints[cur_gap_idx]
        if hint != '':
            c.print(c.mark_info('Hint: ') + hint)
            c.print()

    # user_input
    if state.user_input is not None:
        c.print(state.user_input)
        c.print()

    # correctness_indicator
    match state.correctness_indicator:
        case True:
            c.success('V')
            c.print()
        case False:
            c.error('X')
            c.print()

    # answer for curr gap
    if state.show_answer and cur_gap_idx is not None:
        c.info(f'The answer for the gap #{cur_gap_idx + 1} is:')
        c.print()
        c.print(state.answers[cur_gap_idx])
        c.print()
        note = state.notes[cur_gap_idx]
        if note != '':
            c.print(c.mark_info('Note: ') + note)
            c.print()

    # error msg
    if state.err_msg is not None:
        c.error(state.err_msg)

    # prompt
    if cur_gap_idx is None:
        c.hint('(press Enter to go to the next task)')
    elif state.show_answer:
        c.hint('(press Enter to hide the answer)')
        c.print()


def process_user_input(
        state: FillGapsTaskState,
        user_input: str
) -> FillGapsTaskState:
    def update_state(
            st: FillGapsTaskState,
            first_user_inputs: list[str | None] | None = None,
            user_input: None | str = None,
            correctness_indicator: bool | None = None,
            correct_text_entered: list[bool] | None = None,
            show_answer: bool = False,
            edit_card: bool = False,
            print_stats: bool = False,
            hist_rec: TaskHistRec | None = None,
            err_msg: str | None = None,
            task_continuation: TaskContinuation = TaskContinuation.CONTINUE_TASK,
    ) -> FillGapsTaskState:
        return dataclasses.replace(
            st,
            first_user_inputs=first_defined(first_user_inputs, st.first_user_inputs),
            user_input=user_input,
            correctness_indicator=correctness_indicator,
            correct_text_entered=first_defined(correct_text_entered, st.correct_text_entered),
            show_answer=show_answer,
            edit_card=edit_card,
            print_stats=print_stats,
            hist_rec=first_defined(hist_rec, st.hist_rec),
            err_msg=err_msg,
            task_continuation=task_continuation,
        )

    if state.card_is_valid and not all(state.correct_text_entered):
        cur_gap_idx = state.correct_text_entered.index(False)
    else:
        cur_gap_idx = None

    def process_command(cmd: str) -> FillGapsTaskState:
        nonlocal state
        match cmd:
            case 'e':
                return update_state(state, task_continuation=TaskContinuation.EXIT)
            case 'a' if cur_gap_idx is not None:
                if state.first_user_inputs[cur_gap_idx] is None:
                    first_user_inputs = state.first_user_inputs.copy()
                    first_user_inputs[cur_gap_idx] = ''
                    state = update_state(state, first_user_inputs=first_user_inputs)
                return update_state(state, show_answer=True)
            case 'u':
                return update_state(state, edit_card=True)
            case 's':
                return update_state(state, print_stats=True)
            case _:
                return update_state(state, err_msg=f'Unknown command "{cmd}"')

    if user_input.startswith('`'):
        return process_command(user_input[1:])
    if user_input == '':
        return update_state(state)
    if cur_gap_idx is None:
        if user_input == '':
            return update_state(state, task_continuation=TaskContinuation.NEXT_TASK)
        else:
            return update_state(state)
    if state.first_user_inputs[cur_gap_idx] is None:
        first_user_inputs = state.first_user_inputs.copy()
        first_user_inputs[cur_gap_idx] = user_input
        state = update_state(state, first_user_inputs=first_user_inputs)
    if user_input != state.answers[cur_gap_idx]:
        return update_state(state, correctness_indicator=False)
    else:
        num_of_gaps = len(state.answers)
        if cur_gap_idx == num_of_gaps - 1:
            mark = (sum(1 if state.first_user_inputs[i] == state.answers[i] else 0 for i in range(num_of_gaps))
                    / num_of_gaps)
            note = ' | '.join(f'exp: {state.answers[i]} & act: {state.first_user_inputs[i]}' for i in range(num_of_gaps))
            state = update_state(state, hist_rec=TaskHistRec(time=None, task_id=state.task.id, mark=mark, note=note))
        correct_text_entered = state.correct_text_entered
        correct_text_entered[cur_gap_idx] = True
        return update_state(state, correct_text_entered=correct_text_entered)
