import re
import tkinter as tk
from ctypes import windll
from tkinter import ttk
from typing import Callable
from uuid import uuid4

from remem.app_context import AppCtx
from remem.commands import CollectionOfCommands
from remem.common import Try, try_
from remem.console import select_single_option
from remem.dao import insert_folder, select_folder, delete_folder, insert_card, select_all_queries, insert_query, \
    update_query, delete_query, select_card, update_card
from remem.dtos import CardTranslate, AnyCard, Query, Folder, CardFillGaps
from remem.ui import render_add_card_view, render_card_translate, render_query, open_dialog, render_card_fill

windll.shcore.SetProcessDpiAwareness(1)


def cmd_make_new_folder(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    name = c.input("New folder name: ").strip()
    if name == '':
        c.error('Folder name must not be empty')
        return
    curr_folder_path = cache.get_curr_folder_path()
    new_folder_id = insert_folder(
        db.con, Folder(parent_id=curr_folder_path[-1].id if len(curr_folder_path) > 0 else None, name=name))
    c.success('A folder created')
    c.info(f'{name}:{new_folder_id}')


def cmd_show_current_folder(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    print(c.mark_info('Current folder: '), end='')
    print('/' + '/'.join([f'{f.name}:{f.id}' for f in cache.get_curr_folder_path()]))


def cmd_list_all_folders(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    c.info('List of all folders:')
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
        print(f'{"    " * r['level']}{r['name']}:{r['id']}')


def cmd_select_folder_by_id(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    inp = c.input("id of the folder to select: ").strip()
    cache.set_curr_folder(None if inp == '' else int(inp))
    cmd_show_current_folder(ctx)


def cmd_delete_folder_by_id(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    folder_id = int(c.input("id of the folder to delete: ").strip())
    folder = select_folder(db.con, folder_id)
    if folder is None:
        c.error(f'The folder with id of {folder_id} does not exist.')
    else:
        delete_folder(db.con, folder_id)
        c.success('The folder was deleted.')
        if folder_id in {f.id for f in cache.get_curr_folder_path()}:
            cache.set_curr_folder(None)
            cmd_show_current_folder(ctx)


def prepare_card_for_insert(ctx: AppCtx, card: AnyCard) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    card.base.ext_id = str(uuid4())
    curr_folder_path = cache.get_curr_folder_path()
    if len(curr_folder_path) > 0:
        card.base.folder_id = curr_folder_path[-1].id
    if isinstance(card, CardTranslate):
        card.base.card_type_id = cache.card_types_si['translate']
    else:
        raise Exception(f'Unexpected card type: {card}')


def cmd_add_card(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache

    def do_insert_card(card: AnyCard) -> None:
        prepare_card_for_insert(ctx, card)
        if isinstance(card, CardTranslate):
            cache.set_card_tran_lang1_id(card.lang1_id)
            cache.set_card_tran_lang2_id(card.lang2_id)
            cache.set_card_tran_read_only1(card.read_only1)
            cache.set_card_tran_read_only2(card.read_only2)
        with db.transaction() as tr:
            insert_card(tr, card)

    def do_save_card(crd: AnyCard) -> Try[None]:
        return try_(lambda: do_insert_card(crd))

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
        on_card_save=do_save_card,
    ).grid()
    root.mainloop()


def cmd_edit_card_by_id(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    card_id = int(c.input('Enter id of the card to edit: '))
    card = select_card(db.con, cache, card_id)
    if card is None:
        c.error(f'The card with id of {card_id} doesn\'t exist.')
        return

    def save_card(crd: AnyCard, close_dialog: Callable[[], None]) -> Try[None]:
        res = try_(lambda: update_card(db.con, crd))
        if res.is_success():
            close_dialog()
        return res

    if isinstance(card, CardTranslate):
        open_dialog(
            title=f'Edit Translate Card',
            render=lambda parent, close_dialog: render_card_translate(
                cache, parent, is_edit=True, card=card,
                on_save=lambda crd: save_card(crd, close_dialog),
            )
        )
    elif isinstance(card, CardFillGaps):
        open_dialog(
            title=f'Edit Fill Gaps Card',
            render=lambda parent, close_dialog: render_card_fill(
                cache, parent, is_edit=True, card=card,
                on_save=lambda crd: save_card(crd, close_dialog),
            )
        )
    else:
        raise Exception(f'Unexpected type of card: {card}')


def cmd_list_all_queries(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    c.info(f'List of all queries:')
    for q in select_all_queries(db.con):
        print(q.name)


def cmd_add_query(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache

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


def cmd_edit_query(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
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


def cmd_delete_query(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
    all_queries = select_all_queries(db.con)
    print(c.mark_prompt('Select a query to delete:'))
    idx = select_single_option([q.name for q in all_queries])
    if idx is None:
        return
    query_to_delete = all_queries[idx]

    delete_query(db.con, query_to_delete.id)
    c.info('The query has been deleted.')


def cmd_run_query(ctx: AppCtx) -> None:
    c, db, cache = ctx.c, ctx.db, ctx.cache
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


def add_data_commands(ctx: AppCtx, commands: CollectionOfCommands) -> None:
    def add_command(name: str, cmd: Callable[[AppCtx], None]) -> None:
        commands.add_command(name, lambda: cmd(ctx))

    add_command('make new folder', cmd_make_new_folder)
    add_command('show current folder', cmd_show_current_folder)
    add_command('list all folders', cmd_list_all_folders)
    add_command('select folder by id', cmd_select_folder_by_id)
    add_command('delete folder by id', cmd_delete_folder_by_id)

    add_command('add card', cmd_add_card)
    add_command('edit card', cmd_edit_card_by_id)

    add_command('add query', cmd_add_query)
    add_command('list all queries', cmd_list_all_queries)
    add_command('edit query', cmd_edit_query)
    add_command('run query', cmd_run_query)
    add_command('delete query', cmd_delete_query)
