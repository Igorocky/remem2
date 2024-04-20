import dataclasses
from dataclasses import dataclass, field

from remem.cache import Cache
from remem.common import first_defined
from remem.console import Console
from remem.constants import TaskTypes
from remem.dtos import Task, CardTranslate, TaskHistRec, AnyCard
from remem.repeat import TaskContinuation, RepeatTaskState


@dataclass
class CardTranslateSide:
    lang_str: str = ''
    read_only: int = 0
    text: str = ''
    tran: str = ''


@dataclass
class TranslateTaskState(RepeatTaskState):
    src: CardTranslateSide = field(default_factory=lambda: CardTranslateSide())
    dst: CardTranslateSide = field(default_factory=lambda: CardTranslateSide())
    first_user_translation: None | str = None
    user_translation: None | str = None
    correctness_indicator: bool | None = None
    correct_translation_entered: bool = False
    enter_mark: bool = False
    err_msg: str | None = None


def get_card_translate_side(cache: Cache, card: CardTranslate, dir12: bool, src: bool) -> CardTranslateSide:
    if dir12 and src or not dir12 and not src:
        return CardTranslateSide(
            lang_str=cache.lang_is[card.lang1_id],
            read_only=card.read_only1,
            text=card.text1,
            tran=card.tran1
        )
    else:
        return CardTranslateSide(
            lang_str=cache.lang_is[card.lang2_id],
            read_only=card.read_only2,
            text=card.text2,
            tran=card.tran2
        )


def make_initial_state(cache: Cache, card: AnyCard, task: Task) -> TranslateTaskState:
    if not isinstance(card, CardTranslate):
        raise Exception(f'CardTranslate was expected but got {card}')
    dir12 = task.task_type_id == cache.task_types_si[TaskTypes.translate_12]
    src = get_card_translate_side(cache, card, dir12=dir12, src=True)
    dst = get_card_translate_side(cache, card, dir12=dir12, src=False)
    return TranslateTaskState(task=task, src=src, dst=dst)


def read_mark(c: Console) -> float:
    while True:
        try:
            inp = c.input('Your mark [1.0]: ')
            if inp.strip() == '':
                return 1.0
            mark = float(inp)
            return min(max(0.0, mark), 1.0)
        except ValueError:
            pass


def render_state(c: Console, state: TranslateTaskState) -> None:
    # commands
    show_answer_cmd_descr = '' if state.dst.read_only or state.correct_translation_entered or state.show_answer \
        else 'a - show answer    '
    c.hint(f'{show_answer_cmd_descr}e - exit    u - update card    s - show statistics')
    c.print()

    # question
    if state.dst.read_only:
        c.prompt(f'Recall translation to {state.dst.lang_str} for:')
    else:
        c.prompt(f'Write translation to {state.dst.lang_str} for:')
    c.print()
    c.print(state.src.text)
    c.print()

    # translation
    if state.user_translation is not None:
        c.print(state.user_translation)
        c.print()
    elif state.correct_translation_entered:
        c.print(state.dst.text)
        c.print()

    # correctness_indicator
    match state.correctness_indicator:
        case True:
            c.success('V')
            c.print()
        case False:
            c.error('X')
            c.print()
        case _ if state.correct_translation_entered:
            c.success('V')
            c.print()

    # answer
    if state.show_answer or state.dst.read_only and state.first_user_translation is not None:
        c.info('Translation:')
        c.print()
        c.print(state.dst.text)
        c.print()

    # transcription
    if (state.dst.tran != ''
            and (state.show_answer
                 or state.correct_translation_entered
                 or state.dst.read_only and state.first_user_translation is not None)):
        c.print(c.mark_info('Transcription: ') + state.dst.tran)
        c.print()

    # error message
    if state.err_msg is not None:
        c.error(state.err_msg)
        c.print()

    # prompt
    if state.enter_mark:
        c.print(c.mark_prompt('Enter mark [1]: '), end='')
    elif state.correct_translation_entered:
        c.print(c.mark_prompt('(press Enter to go to the next task)'), end='')
    elif state.show_answer:
        c.print(c.mark_prompt('(press Enter to hide the answer)'))
        c.print()


def process_user_input(
        state: TranslateTaskState,
        user_input: str
) -> TranslateTaskState:
    def update_state(
            st: TranslateTaskState,
            first_user_translation: None | str = None,
            user_translation: None | str = None,
            correctness_indicator: bool | None = None,
            correct_translation_entered: bool = False,
            enter_mark: bool = False,
            show_answer: bool = False,
            edit_card: bool = False,
            print_stats: bool = False,
            hist_rec: TaskHistRec | None = None,
            err_msg: str | None = None,
            task_continuation: TaskContinuation = TaskContinuation.CONTINUE_TASK,
    ) -> TranslateTaskState:
        return dataclasses.replace(
            st,
            first_user_translation=first_defined(first_user_translation, st.first_user_translation),
            user_translation=user_translation,
            correctness_indicator=correctness_indicator,
            correct_translation_entered=correct_translation_entered or st.correct_translation_entered,
            enter_mark=enter_mark or st.enter_mark,
            show_answer=show_answer,
            edit_card=edit_card,
            print_stats=print_stats,
            hist_rec=first_defined(hist_rec, st.hist_rec),
            err_msg=err_msg,
            task_continuation=task_continuation
        )

    def process_command(cmd: str) -> TranslateTaskState:
        match cmd:
            case 'e':
                return update_state(state, task_continuation=TaskContinuation.EXIT)
            case 'a' if not state.dst.read_only:
                if state.first_user_translation is None:
                    return update_state(
                        state, first_user_translation='', show_answer=True,
                        hist_rec=TaskHistRec(time=None, task_id=state.task.id, mark=0.0, note=''))
                else:
                    return update_state(state, show_answer=True)
            case 'u':
                return update_state(state, edit_card=True)
            case 's':
                return update_state(state, print_stats=True)
            case _:
                return update_state(state, err_msg=f'Unknown command "{cmd}"')

    if state.enter_mark:
        try:
            user_input = user_input.strip()
            if user_input.startswith('`'):
                return process_command(user_input[1:])
            mark = 1.0 if user_input == '' else float(user_input)
            if not (0.0 <= mark <= 1.0):
                return update_state(state, enter_mark=True,
                                    err_msg='The mark must be between 0.0 and 1.0 (inclusively)')
            return update_state(state, correct_translation_entered=True, task_continuation=TaskContinuation.NEXT_TASK,
                                hist_rec=TaskHistRec(time=None, task_id=state.task.id, mark=mark, note=''))
        except ValueError:
            return update_state(state)
    if user_input.startswith('`'):
        return process_command(user_input[1:])
    if state.correct_translation_entered:
        if user_input == '':
            return update_state(state, task_continuation=TaskContinuation.NEXT_TASK)
        else:
            return update_state(state)
    if state.dst.read_only:
        return update_state(state, first_user_translation='', enter_mark=True)
    if user_input == '':
        return update_state(state)
    if state.first_user_translation is None:
        mark = 1.0 if user_input == state.dst.text else 0.0
        state = update_state(state, first_user_translation=user_input,
                             hist_rec=TaskHistRec(time=None, task_id=state.task.id, mark=mark, note=user_input))
    if user_input != state.dst.text:
        return update_state(state, user_translation=user_input, correctness_indicator=False)
    else:
        return update_state(state, user_translation=user_input, correctness_indicator=True,
                            correct_translation_entered=True)
