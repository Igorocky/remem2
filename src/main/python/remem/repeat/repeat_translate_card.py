import dataclasses
from dataclasses import dataclass, field

from remem.app_context import AppCtx
from remem.cache import Cache
from remem.console import Console
from remem.constants import TaskTypes
from remem.dao import select_card, insert_task_hist
from remem.dtos import Task, CardTranslate, TaskHistRec
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


def make_initial_state(ctx: AppCtx, task: Task) -> TranslateTaskState:
    con = ctx.database.con
    cache = ctx.cache
    card = select_card(con, cache, task.card_id)
    if not isinstance(card, CardTranslate):
        raise Exception(f'CardTranslate was expected but got {card}')
    dir12 = task.task_type_id == cache.task_types_si[TaskTypes.translate_12]
    src = get_card_translate_side(cache, card, dir12=dir12, src=True)
    dst = get_card_translate_side(cache, card, dir12=dir12, src=False)
    return TranslateTaskState(task=task, src=src, dst=dst, )


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


def render_state(ctx: AppCtx, state: TranslateTaskState) -> None:
    c = ctx.console

    def rnd_commands() -> None:
        show_answer_cmd_descr = 'a - show answer    ' if not state.dst.read_only else ''
        c.hint(f'{show_answer_cmd_descr}e - exit    u - update card    s - show statistics\n')

    def rnd_question() -> None:
        if state.dst.read_only:
            print(c.mark_prompt(f'Recall translation to {state.dst.lang_str} for:\n'))
        else:
            print(c.mark_prompt(f'Write translation to {state.dst.lang_str} for:\n'))
        print(state.src.text + '\n')

    def rnd_answer() -> None:
        if (state.show_answer
                or state.dst.read_only and state.first_user_translation is not None
                or state.correct_translation_entered):
            if not state.dst.read_only and state.first_user_translation != state.dst.text:
                c.info('The translation is:\n')
            print(state.dst.text + '\n')
            if state.dst.tran != '':
                print(c.mark_info('Transcription: ') + state.dst.tran + '\n')

    def rnd_user_translation() -> None:
        if state.user_translation is not None:
            print(state.user_translation)

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
            first_user_translation=first_user_translation or state.first_user_translation,
            user_translation=user_translation,
            correctness_indicator=correctness_indicator,
            correct_translation_entered=correct_translation_entered or state.correct_translation_entered,
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
