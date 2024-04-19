import dataclasses
from dataclasses import dataclass, field

from remem.cache import Cache
from remem.common import extract_gaps_from_text
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


def render_state(c: Console, state: FillGapsTaskState) -> None:
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
            c.print(f'{status} #{i + 1} {answer}')
            if note != '':
                c.print(f'    {note}')
        if cur_gap_idx is None and state.card.notes != '':
            c.print()
            c.print('Notes:')
            c.print(state.card.notes)

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
        c.print()
        c.print(' '.join(text_arr).strip())
        if cur_gap_idx is not None:
            hint = state.hints[cur_gap_idx]
            if hint != '':
                c.print()
                c.print(c.mark_info('Hint: ') + hint)

    def rnd_answer_for_curr_gap() -> None:
        if state.show_answer and cur_gap_idx is not None:
            c.info(f'The answer for the gap #{cur_gap_idx + 1} is:\n')
            c.print(state.answers[cur_gap_idx])
            note = state.notes[cur_gap_idx]
            if note != '':
                c.print()
                c.print(c.mark_info('Note: ') + note)

    def rnd_user_input() -> None:
        if state.user_input is not None:
            c.print(state.user_input)

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
        c.print()
        rnd_answers()
        c.print()
        rnd_question()
        c.print()
        rnd_answer_for_curr_gap()
        c.print()
        rnd_user_input()
        c.print()
        rnd_indicator()
        c.print()
        rnd_err_msg()
    c.print()
    rnd_prompt()


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
            first_user_inputs=first_user_inputs or st.first_user_inputs,
            user_input=user_input,
            correctness_indicator=correctness_indicator,
            correct_text_entered=correct_text_entered or st.correct_text_entered,
            show_answer=show_answer,
            edit_card=edit_card,
            print_stats=print_stats,
            hist_rec=hist_rec or st.hist_rec,
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
                return update_state(state, task_continuation=TaskContinuation.EXIT)
            case 'a' if cur_gap_idx is not None:
                if state.first_user_inputs[cur_gap_idx] is None:
                    first_user_inputs = state.first_user_inputs.copy()
                    first_user_inputs[cur_gap_idx] = ''
                    return update_state(state, first_user_inputs=first_user_inputs, show_answer=True)
                return update_state(state, show_answer=True)
            case 'u':
                return update_state(state, edit_card=True)
            case 's':
                return update_state(state, print_stats=True)
            case _:
                return update_state(state, err_msg=f'Unknown command "{cmd}"')

    if user_input.startswith('`'):
        return process_command(user_input[1:])
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
        return update_state(state, correctness_indicator=False if user_input != '' else None)
    else:
        num_of_gaps = len(state.answers)
        if cur_gap_idx == num_of_gaps - 1:
            mark = (sum(1 if state.first_user_inputs[i] == state.answers[i] else 0 for i in range(num_of_gaps))
                    / num_of_gaps)
            note = ' '.join(f'exp: {state.answers[i]} & act: {state.first_user_inputs[i]}' for i in range(num_of_gaps))
            state = update_state(state, hist_rec=TaskHistRec(time=None, task_id=state.task.id, mark=mark, note=note))
        correct_text_entered = state.correct_text_entered
        correct_text_entered[cur_gap_idx] = True
        return update_state(state, correctness_indicator=True, correct_text_entered=correct_text_entered)
