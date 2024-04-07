from dataclasses import dataclass
from enum import Enum

from remem.app_context import AppCtx
from remem.cache import Cache
from remem.console import Console, clear_screen
from remem.constants import TaskTypes
from remem.dao import select_card, insert_task_hist
from remem.dtos import Task, CardTranslate, TaskHistRec


@dataclass
class CardTranslateSide:
    lang_str: str = ''
    read_only: int = 0
    text: str = ''
    tran: str = ''


@dataclass
class TranslateTaskState:
    task: Task
    src: CardTranslateSide
    dst: CardTranslateSide
    first_user_translation: None | str = None
    correct_translation_entered: bool = False


class TranslateTaskAction(Enum):
    EXIT = 1
    CONTINUE = 2


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


def ask_to_press_enter(c: Console) -> None:
    input(c.mark_prompt('\nPress Enter'))


def process_user_input(
        ctx: AppCtx,
        state: TranslateTaskState,
        user_input: str
) -> TranslateTaskAction:
    c = ctx.console
    con = ctx.database.con
    if user_input.startswith('`'):
        cmd = user_input[1:]
        match cmd:
            case 'e':
                return TranslateTaskAction.EXIT
            case 'a':
                if state.first_user_translation is None:
                    insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=0.0, note=''))
                    state.first_user_translation = ''
                print('Translation:\n')
                print(state.dst.text)
                ask_to_press_enter(c)
                return TranslateTaskAction.CONTINUE
            case _:
                c.error(f'Unknown command "{cmd}"')
                ask_to_press_enter(c)
                return TranslateTaskAction.CONTINUE
    if user_input != state.dst.text:
        if state.first_user_translation is None:
            insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=0.0, note=user_input))
            state.first_user_translation = user_input
        c.error('X')
        ask_to_press_enter(c)
        return TranslateTaskAction.CONTINUE
    else:
        if state.first_user_translation is None:
            insert_task_hist(con, TaskHistRec(time=None, task_id=state.task.id, mark=1.0, note=user_input))
            state.first_user_translation = user_input
        c.success('V')
        ask_to_press_enter(c)
        return TranslateTaskAction.EXIT


def render_state(ctx: AppCtx, state: TranslateTaskState) -> None:
    c = ctx.console
    c.hint(f'a - show answer       e - exit')
    if state.src.read_only:
        print(c.mark_prompt(f'Recall translation to {state.dst.lang_str} for:'))
    else:
        print(c.mark_prompt(f'Write translation to {state.dst.lang_str} for:'))
    print(state.src.text)


def repeat_translate_task(ctx: AppCtx, task: Task) -> None:
    state = make_initial_state(ctx, task)
    while True:
        render_state(ctx, state)
        match process_user_input(ctx, state, input()):
            case TranslateTaskAction.CONTINUE:
                clear_screen()
            case TranslateTaskAction.EXIT:
                return
