import re
import tkinter as tk
from ctypes import windll
from sqlite3 import Cursor
from tkinter import ttk
from typing import Callable
from uuid import uuid4

from remem.cache import Cache
from remem.commands import CollectionOfCommands
from remem.common import Try, try_
from remem.console import Console, select_single_option
from remem.constants import CardTypes
from remem.dao import insert_folder, select_folder, delete_folder, insert_card, select_all_queries, insert_query, \
    update_query, delete_query, select_card
from remem.database import Database
from remem.dtos import CardTranslate, AnyCard, Query, Task, Folder, CardFillGaps
from remem.ui import render_add_card_view, render_card_translate, render_query, open_dialog

windll.shcore.SetProcessDpiAwareness(1)


def cmd_make_new_folder(c: Console, db: Database, cache: Cache) -> None:
    name = c.input("New folder name: ").strip()
    if name == '':
        c.error('Folder name must not be empty')
        return
    curr_folder_path = cache.get_curr_folder_path()
    new_folder_id = insert_folder(
        db.con, Folder(parent_id=curr_folder_path[-1].id if len(curr_folder_path) > 0 else None, name=name))
    c.success('A folder created')
    c.info(f'{name}:{new_folder_id}')


def cmd_show_current_folder(c: Console, cache: Cache) -> None:
    print(c.mark_info('Current folder: '), end='')
    print('/' + '/'.join([f'{f.name}:{f.id}' for f in cache.get_curr_folder_path()]))


def cmd_list_all_folders(db: Database) -> None:
    for r in db.con.execute("""
        with recursive folders(level, id, name, parent) as (
            select 0, id, name, parent_id from FOLDER where parent_id is null
            union all
            select pr.level+1, ch.id, ch.name, ch.parent_id
            from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            order by 1 desc
        )
        select level, id, name from folders
    """):
        print(f'{"    " * r['level']}{r['name']}:{r['folder_id']}')


def cmd_select_folder_by_id(c: Console, cache: Cache) -> None:
    inp = c.input("id of the folder to select: ").strip()
    cache.set_curr_folder(None if inp == '' else int(inp))
    cmd_show_current_folder(c, cache)


def cmd_delete_folder_by_id(c: Console, db: Database, cache: Cache) -> None:
    folder_id = int(c.input("id of the folder to delete: ").strip())
    folder = select_folder(db.con, folder_id)
    if folder is None:
        c.error(f'The folder with id of {folder_id} does not exist.')
    else:
        delete_folder(db.con, folder_id)
        c.success('The folder was deleted.')
        if folder_id in {f.id for f in cache.get_curr_folder_path()}:
            cache.set_curr_folder(None)
            cmd_show_current_folder(c, cache)


def prepare_card_for_insert(cache: Cache, card: AnyCard) -> None:
    card.base.ext_id = str(uuid4())
    curr_folder_path = cache.get_curr_folder_path()
    if len(curr_folder_path) > 0:
        card.base.folder_id = curr_folder_path[-1].id
    if isinstance(card, CardTranslate):
        card.base.card_type_id = cache.card_types_si['translate']
    else:
        raise Exception(f'Unexpected card type: {card}')


def cmd_add_card(c: Console, db: Database, cache: Cache) -> None:
    def do_insert_card(card: AnyCard) -> None:
        prepare_card_for_insert(cache, card)
        if isinstance(card, CardTranslate):
            cache.set_card_tran_lang1_id(card.lang1_id)
            cache.set_card_tran_lang2_id(card.lang2_id)
            cache.set_card_tran_read_only1(card.read_only1)
            cache.set_card_tran_read_only2(card.read_only2)
        with db.transaction() as tr:
            insert_card(tr, card)

    if len(cache.get_curr_folder_path()) == 0:
        c.error('Cannot create a card in the root folder.')
        return
    root = tk.Tk()
    root.title('Add card')
    root_frame = ttk.Frame(root)
    root_frame.grid()
    render_add_card_view(
        cache,
        parent=root_frame,
        on_card_save=lambda card: try_(lambda crd: do_insert_card(crd)),
    ).grid()
    root.mainloop()


# def edit_translate_card(db: Database, cache: Cache, card_id: int) -> None:
#     cursor = db.con.execute("""
#         select lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2
#         from CARD_TRAN
#         where id = :card_id
#     """, {'card_id': card_id})
#     col_idxs = description_to_col_idxs(cursor)
#     row = cursor.fetchone()
#     card = CardTranslate(
#         id=card_id,
#         lang1_str=cache.lang_is[row[col_idxs['lang1_id']]],
#         lang2_str=cache.lang_is[row[col_idxs['lang2_id']]],
#         readonly1=row[col_idxs['read_only1']] != 0,
#         readonly2=row[col_idxs['read_only2']] != 0,
#         text1=row[col_idxs['text1']],
#         text2=row[col_idxs['text2']],
#         tran1=row[col_idxs['tran1']],
#         tran2=row[col_idxs['tran2']],
#     )
#
#     def on_save(card1: CardTranslate, close_dialog: Callable[[], None]) -> Try[None]:
#         res = update_card_translate(db, cache, card1)
#         if res.is_success():
#             close_dialog()
#         return res
#
#     open_dialog(
#         title='Edit Translate Card',
#         render_form=lambda parent, close_dialog: render_card_translate(
#             parent, langs=list(cache.lang_si),
#             card=card,
#             is_edit=True,
#             on_save=lambda card1: on_save(card1, close_dialog),
#         )
#     )


# def edit_fill_card(c: Console, db: Database, cache: Cache, card_id: int) -> None:
#     pass


def cmd_edit_card_by_id(c: Console, db: Database, cache: Cache) -> None:
    card_id = int(c.input('Enter id of the card to edit: '))
    card = select_card(db.con, cache, card_id)
    if card is None:
        c.error(f'The card with id of {card_id} doesn\'t exist.')
        return
    if isinstance(card, CardTranslate):
        card_type = 'Translate'
    elif isinstance(card, CardFillGaps):
        card_type = 'Fill Gaps'
    else:
        raise Exception(f'Unexpected type of card: {card}')
    open_dialog(
        title=f'Edit {card_type} Card',
        render_form=lambda parent, close_dialog: render_card_translate(
            parent, langs=list(cache.lang_si),
            card=card,
            is_edit=True,
            on_save=lambda card1: on_save(card1, close_dialog),
        )
    )
    card_type_id = db.con.execute("""
        select card_type_id from CARD where id = :card_id
    """, {'card_id': card_id}).fetchone()[0]
    if card_type_id == cache.card_types_si[CardTypes.translate]:
        edit_translate_card(db, cache, card_id)
    elif card_type_id == cache.card_types_si[CardTypes.fill_gaps]:
        edit_fill_card(c, db, cache, card_id)
    else:
        raise Exception(f'Unexpected type of card {card_type_id}.')


def cmd_list_all_queries(c: Console, db: Database) -> None:
    c.info(f'List of all queries:')
    for q in select_all_queries(db.con):
        print(q.name)


def cmd_add_query(db: Database) -> None:
    def save_query(query: Query) -> Try[None]:
        def do() -> None:
            insert_query(db.con, query)

        return try_(do)

    root = tk.Tk()
    root.title('Add a new query')
    root_frame = ttk.Frame(root)
    root_frame.grid()
    render_query(
        parent=root_frame,
        is_edit=False,
        on_save=save_query,
    ).grid()
    root.mainloop()


def cmd_edit_query(c: Console, db: Database) -> None:
    all_queries = select_all_queries(db.con)
    print(c.mark_prompt('Select a query to edit:'))
    idx = select_single_option([q.name for q in all_queries])
    if idx is None:
        return
    query_to_edit = all_queries[idx]

    def on_save(query: Query, close_dialog: Callable[[], None]) -> Try[None]:
        res = try_(lambda: update_query(db.con, query))
        if res.is_success():
            close_dialog()
        return res

    open_dialog(
        title='Edit Query',
        render=lambda parent, close_dialog: render_query(
            parent,
            query=query_to_edit,
            is_edit=True,
            on_save=lambda q: on_save(q, close_dialog),
        )
    )


def cmd_delete_query(c: Console, db: Database) -> None:
    all_queries = select_all_queries(db.con)
    print(c.mark_prompt('Select a query to delete:'))
    idx = select_single_option([q.name for q in all_queries])
    if idx is None:
        return
    query_to_delete = all_queries[idx]

    delete_query(db.con, query_to_delete.id)
    c.info('The query has been deleted.')


def cmd_run_query(c: Console, db: Database) -> None:
    all_queries = select_all_queries(db.con)
    print(c.mark_prompt('Select a query to run:'))
    idx = select_single_option([q.name for q in all_queries])
    if idx is None:
        return
    query = all_queries[idx]
    param_names = sorted(set(m.group(1) for m in re.finditer(r':([a-z0-9_]+)', query.text)))
    if len(param_names) > 0:
        print(c.mark_prompt('Enter parameter values:'))
    params = {}
    for param_name in param_names:
        params[param_name] = c.input(f'{param_name}: ')
    cur = db.con.execute(all_queries[idx].text, params)
    col_names: list[str] = [c[0] for c in cur.description]
    col_width = [len(c) for c in col_names]
    result = [[str(c) for c in r.values()] for r in cur]
    for r in result:
        for i, v in enumerate(r):
            col_width[i] = max(col_width[i], len(v))
    header = ' '.join([h.ljust(col_width[i]) for i, h in enumerate(col_names)])
    print('-' * len(header))
    print(header)
    print('-' * len(header))
    for row in result:
        print(' '.join([c.ljust(col_width[i]) for i, c in enumerate(row)]))
    print('-' * len(header))


def add_dao_commands(c: Console, db: Database, commands: CollectionOfCommands) -> None:
    cache = Cache(db)
    commands.add_command('make new folder', lambda: cmd_make_new_folder(c, db, cache))
    commands.add_command('show current folder', lambda: cmd_show_current_folder(c, cache))
    commands.add_command('list all folders', lambda: cmd_list_all_folders(db))
    commands.add_command('go to folder by id', lambda: cmd_select_folder_by_id(c, cache))
    commands.add_command('delete folder by id', lambda: cmd_delete_folder_by_id(c, db, cache))
    commands.add_command('add card', lambda: cmd_add_card(c, db, cache))
    commands.add_command('edit card', lambda: cmd_edit_card_by_id(c, db, cache))

    commands.add_command('add query', lambda: cmd_add_query(db))
    commands.add_command('list all queries', lambda: cmd_list_all_queries(c, db))
    commands.add_command('edit query', lambda: cmd_edit_query(c, db))
    commands.add_command('run query', lambda: cmd_run_query(c, db))
    commands.add_command('delete query', lambda: cmd_delete_query(c, db))
