import dataclasses
from dataclasses import dataclass
from typing import Tuple, Any

from remem.app_context import AppCtx
from remem.cache import Cache
from remem.common import select_folders
from remem.console import Console, clear_screen
from remem.dtos import FolderWithPathDto, AnyCard, CardTranslate, BaseCard, CardFillGaps


@dataclass
class SearchState:
    c: Console
    cache: Cache
    dir: FolderWithPathDto | None = None
    text: str | None = None


def make_initial_state(c: Console, cache: Cache) -> SearchState:
    return SearchState(c=c, cache=cache)


def render_state(c: Console, state: SearchState) -> None:
    c.print('1. Text')
    c.print('None' if state.text is None else state.text)

    c.print()
    c.print('2. Folder')
    c.print('None' if state.dir is None else state.dir.path)

    c.print()


def process_user_input(
        state: SearchState,
        user_input: str
) -> SearchState:
    c = state.c
    if user_input == '1':
        c.print()
        new_text = c.input('Enter text to search for: ').strip().lower()
        return dataclasses.replace(state, text=None if len(new_text) == 0 else new_text)
    elif user_input == '2':
        c.print()
        selected_folders = select_folders(c, state.cache.get_all_folders(), 'Folder name: ', single=True)
        if selected_folders is None:
            return state
        else:
            return dataclasses.replace(state, dir=None if len(selected_folders) == 0 else selected_folders[0])
    else:
        return state


def get_subdict_by_key_prefix(d: dict[str, Any], pref: str) -> dict[str, Any]:
    res = {}
    pref_len = len(pref)
    for k in d:
        if k.startswith(pref):
            res[k[pref_len:]] = d[k]
    return res


def load_card(row: dict[str, Any]) -> AnyCard:
    if row['ct_id'] is not None:
        return CardTranslate(
            base=BaseCard(**get_subdict_by_key_prefix(row, 'c_')),
            **get_subdict_by_key_prefix(row, 'ct_')
        )
    elif row['cf_id'] is not None:
        return CardFillGaps(
            base=BaseCard(**get_subdict_by_key_prefix(row, 'c_')),
            **get_subdict_by_key_prefix(row, 'cf_')
        )
    else:
        raise Exception(f'Cannot convert a row to an AnyCard: {row=}')


def prepare_query_and_params(state: SearchState) -> Tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {}
    if state.dir is None:
        folder_condition = '1 = 1'
    else:
        folder_condition = f"""
            c.folder_id in (
                with recursive folders(id) as (
                    select id from FOLDER where id = :folder_id
                    union all
                    select ch.id from folders pr inner join FOLDER ch on pr.id = ch.parent_id
                )
                select id from folders
            )
        """
        params['folder_id'] = state.dir.id
    if state.text is None:
        text_condition = '1 = 1'
    else:
        text_condition = f"""
            lower(ct.text1) like lower('%'||:text||'%')
            or lower(ct.text2) like lower('%'||:text||'%')
            or lower(ct.notes) like lower('%'||:text||'%')
            or lower(cf.descr) like lower('%'||:text||'%')
            or lower(cf.text) like lower('%'||:text||'%')
            or lower(cf.notes) like lower('%'||:text||'%')
        """
        params['text'] = state.text
    query = f"""
        select
            c.id c_id, c.ext_id c_ext_id, c.folder_id c_folder_id, c.card_type_id c_card_type_id, c.crt_time c_crt_time,
            ct.id ct_id, ct.lang1_id ct_lang1_id, ct.read_only1 ct_read_only1, ct.text1 ct_text1, 
                ct.lang2_id ct_lang2_id, ct.read_only2 ct_read_only2, ct.text2 ct_text2, ct.notes ct_notes,
            cf.id cf_id, cf.lang_id cf_lang_id, cf.descr cf_descr, cf.text cf_text, cf.notes cf_notes
        from 
            CARD c
            left join CARD_TRAN CT on c.id = CT.id
            left join CARD_FILL CF on c.id = CF.id
        where ({folder_condition}) and ({text_condition})
    """
    return query, params


def card_to_str(card: AnyCard, cache: Cache) -> str:
    if isinstance(card, CardTranslate):
        text1_ro = '(ro)' if card.read_only1 else ''
        text2_ro = '(ro)' if card.read_only2 else ''
        return (f"Translate:"
                f" {cache.lang_is[card.lang1_id]}{text1_ro}: {card.text1}"
                f" {cache.lang_is[card.lang2_id]}{text2_ro}: {card.text2}"
                f" notes: {card.notes} ")
    elif isinstance(card, CardFillGaps):
        return (f"Fill gaps [{cache.lang_is[card.lang_id]}]: "
                f" descr: {card.descr}"
                f" text: {card.text}"
                f" notes: {card.notes}")
    else:
        raise Exception(f'Unexpected type of card: {card}')


def cmd_search_cards(ctx: AppCtx) -> None:
    c, cache, db = ctx.console, ctx.cache, ctx.database
    state = make_initial_state(c, cache)
    clear_screen()
    render_state(c, state)
    prompt = 'Press Enter to search or select a parameter number to change it: '
    user_input = c.input(prompt).strip()
    while user_input != '':
        state = process_user_input(state, user_input)
        clear_screen()
        render_state(c, state)
        user_input = c.input(prompt).strip()
    clear_screen()
    print(f'Search results for text={state.text} folder={state.dir.path if state.dir is not None else "None"}')
    query, params = prepare_query_and_params(state)
    cards = [load_card(r) for r in db.con.execute(query, params)]
    for card in cards:
        print(f'{c.mark_info(str(card.id))} {card_to_str(card, cache)}')
