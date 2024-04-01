import tkinter as tk
from ctypes import windll
from sqlite3 import Connection, Cursor
from tkinter import ttk
from typing import Callable
from uuid import uuid4

from remem.cache import Cache
from remem.commands import CollectionOfCommands
from remem.common import Try, try_
from remem.console import Console
from remem.database import Database
from remem.dtos import CardTranslate, CardFillGaps, Card, Query
from remem.ui import render_add_card_view, render_card_translate, render_query

windll.shcore.SetProcessDpiAwareness(1)


def get_last_id(con: Connection) -> int:
    return int(con.execute('SELECT last_insert_rowid()').fetchone()[0])


def insert_new_folder(con: Connection, *, parent_id: int | None, name: str) -> int:
    con.execute(
        f'insert into FOLDER(parent_id, name) values (:parent_id, :name)',
        {'parent_id': parent_id, 'name': name})
    return get_last_id(con)


def cmd_make_new_folder(c: Console, db: Database, cache: Cache) -> None:
    name = c.input("New folder name: ").strip()
    if name == '':
        c.error('Folder name must not be empty')
        return
    curr_folder_path = cache.get_curr_folder_path()
    insert_new_folder(db.con, parent_id=curr_folder_path[-1].id if len(curr_folder_path) > 0 else None, name=name)
    new_folder_id = get_last_id(db.con)
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
        level = r[0]
        name = r[2]
        folder_id = r[1]
        print(f'{"    " * level}{name}:{folder_id}')


def cmd_go_to_folder_by_id(c: Console, cache: Cache) -> None:
    inp = c.input("id of the folder to go to: ").strip()
    cache.set_curr_folder(None if inp == '' else int(inp))
    cmd_show_current_folder(c, cache)


def cmd_delete_folder_by_id(c: Console, db: Database, cache: Cache) -> None:
    folder_id = int(c.input("id of the folder to delete: ").strip())
    if db.con.execute('select count(1) from FOLDER where id = :folder_id', {'folder_id': folder_id}).fetchone()[0] == 0:
        c.error(f'The folder with id of {folder_id} does not exist.')
    else:
        db.con.execute('delete from FOLDER where id = :folder_id', {'folder_id': folder_id})
        c.success('The folder was deleted.')
        curr_folder_path = cache.get_curr_folder_path()
        if len(curr_folder_path) > 0 and curr_folder_path[-1].id == folder_id:
            cache.set_curr_folder(None if len(curr_folder_path) == 1 else curr_folder_path[-2].id)
            cmd_show_current_folder(c, cache)


def insert_card(con: Connection, card: Card) -> int:
    con.execute(
        'insert into CARD(ext_id, folder_id, card_type_id) values (:ext_id, :folder_id, :card_type_id)',
        {'ext_id': card.ext_id, 'folder_id': card.folder_id, 'card_type_id': card.card_type_id}
    )
    return get_last_id(con)


def set_generic_card_fields(cache: Cache, card: Card) -> Card:
    card.ext_id = str(uuid4())
    curr_folder_path = cache.get_curr_folder_path()
    if len(curr_folder_path) > 0:
        card.folder_id = curr_folder_path[-1].id
    card.card_type_id = cache.card_types_si['translate']
    return card


def set_fields_for_translate_card(cache: Cache, card: CardTranslate) -> None:
    card.lang1_id = cache.lang_si[card.lang1_str]
    card.lang2_id = cache.lang_si[card.lang2_str]


def insert_card_translate(db: Database, cache: Cache, card: CardTranslate) -> Try[None]:
    def do() -> None:
        set_generic_card_fields(cache, card)
        set_fields_for_translate_card(cache, card)
        with db.transaction() as tr:
            card_id = insert_card(con=tr, card=card)
            card.id = card_id
            tr.execute("""
                insert into CARD_TRAN(id, lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2)
                values (:id, :lang1_id, :read_only1, :text1, :tran1, :lang2_id, :read_only2, :text2, :tran2)
            """,
                       {'id': card_id,
                        'lang1_id': card.lang1_id,
                        'read_only1': 1 if card.readonly1 else 0,
                        'text1': card.text1, 'tran1': card.tran1,
                        'lang2_id': card.lang2_id,
                        'read_only2': 1 if card.readonly2 else 0,
                        'text2': card.text2, 'tran2': card.tran2, })
            cache.card_tran_lang1_id = card.lang1_id
            cache.card_tran_lang2_id = card.lang2_id
            cache.card_tran_read_only1 = card.readonly1
            cache.card_tran_read_only2 = card.readonly2

    return try_(do)


def update_card_translate(db: Database, cache: Cache, card: CardTranslate) -> Try[None]:
    def do() -> None:
        set_generic_card_fields(cache, card)
        set_fields_for_translate_card(cache, card)
        db.con.execute("""
            update CARD_TRAN set lang1_id = :lang1_id, read_only1 = :read_only1, text1 = :text1, tran1 = :tran1, 
            lang2_id = :lang2_id, read_only2 = :read_only2, text2 = :text2, tran2 = :tran2
            where id = :card_id
        """, {'card_id': card.id, 'lang1_id': card.lang1_id, 'read_only1': 1 if card.readonly1 else 0,
              'text1': card.text1, 'tran1': card.tran1, 'lang2_id': card.lang2_id,
              'read_only2': 1 if card.readonly2 else 0, 'text2': card.text2, 'tran2': card.tran2, })

    return try_(do)


def insert_card_fill(db: Database, cache: Cache, card: CardFillGaps) -> Try[None]:
    return try_(lambda: None)


def update_card_fill(db: Database, cache: Cache, card: CardFillGaps) -> Try[None]:
    return try_(lambda: None)


def cmd_add_card(c: Console, db: Database, cache: Cache) -> None:
    if len(cache.get_curr_folder_path()) == 0:
        c.error('Cannot create a card in the root folder.')
        return
    root = tk.Tk()
    root.title('Add card')
    root_frame = ttk.Frame(root)
    root_frame.grid()
    render_add_card_view(
        parent=root_frame, langs=list(cache.lang_si),
        card_translate=CardTranslate(
            lang1_str=cache.lang_is[cache.card_tran_lang1_id],
            lang2_str=cache.lang_is[cache.card_tran_lang2_id],
            readonly1=cache.card_tran_read_only1,
            readonly2=cache.card_tran_read_only2,
        ),
        on_card_tr_save=lambda card: insert_card_translate(db=db, cache=cache, card=card),
        card_fill_gaps=CardFillGaps(),
        on_card_fill_save=lambda card: insert_card_fill(db=db, cache=cache, card=card),
    ).grid()
    root.mainloop()


def description_to_col_idxs(cur: Cursor) -> dict[str, int]:
    return {col[0]: i for i, col in enumerate(cur.description)}


def open_edit_card_dialog(title: str, render_form: Callable[[tk.Widget, Callable[[], None]], tk.Widget]) -> None:
    root = tk.Tk()

    def close_dialog() -> None:
        root.destroy()

    root.title(title)
    root_frame = ttk.Frame(root)
    root_frame.grid()
    render_form(root_frame, close_dialog).grid()
    root.mainloop()


def edit_translate_card(db: Database, cache: Cache, card_id: int) -> None:
    cursor = db.con.execute("""
        select lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2
        from CARD_TRAN 
        where id = :card_id
    """, {'card_id': card_id})
    col_idxs = description_to_col_idxs(cursor)
    row = cursor.fetchone()
    card = CardTranslate(
        id=card_id,
        lang1_str=cache.lang_is[row[col_idxs['lang1_id']]],
        lang2_str=cache.lang_is[row[col_idxs['lang2_id']]],
        readonly1=row[col_idxs['read_only1']] != 0,
        readonly2=row[col_idxs['read_only2']] != 0,
        text1=row[col_idxs['text1']],
        text2=row[col_idxs['text2']],
        tran1=row[col_idxs['tran1']],
        tran2=row[col_idxs['tran2']],
    )

    def on_save(card1: CardTranslate, close_dialog: Callable[[], None]) -> Try[None]:
        res = update_card_translate(db, cache, card1)
        if res.is_success():
            close_dialog()
        return res

    open_edit_card_dialog(
        title='Edit Translate Card',
        render_form=lambda parent, close_dialog: render_card_translate(
            parent, langs=list(cache.lang_si),
            card=card,
            is_edit=True,
            on_save=lambda card1: on_save(card1, close_dialog),
        )
    )


def edit_fill_card(c: Console, db: Database, cache: Cache, card_id: int) -> None:
    pass


def cmd_edit_card_by_id(c: Console, db: Database, cache: Cache) -> None:
    card_id = int(c.input('Enter id of the card to edit: '))
    card_type_id = db.con.execute("""
        select card_type_id from CARD where id = :card_id
    """, {'card_id': card_id}).fetchone()[0]
    if card_type_id == cache.card_types_si['translate']:
        edit_translate_card(db, cache, card_id)
    elif card_type_id == cache.card_types_si['fill_gaps']:
        edit_fill_card(c, db, cache, card_id)
    else:
        raise Exception(f'Unexpected type of card {card_type_id}.')


def cmd_list_all_queries(c: Console, db: Database) -> None:
    c.info(f'List of all queries:')
    for r in db.con.execute('select name from QUERY order by name'):
        print(r[0])


def insert_query(con: Connection, query: Query) -> None:
    con.execute(
        'insert into QUERY(name, text) values (:name, :text)',
        {'name': query.name, 'text': query.text}
    )


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
        query=Query(),
        is_edit=False,
        on_save=save_query,
    ).grid()
    root.mainloop()


def add_dao_commands(c: Console, db: Database, commands: CollectionOfCommands) -> None:
    cache = Cache(db)
    commands.add_command('make new folder', lambda: cmd_make_new_folder(c, db, cache))
    commands.add_command('show current folder', lambda: cmd_show_current_folder(c, cache))
    commands.add_command('list all folders', lambda: cmd_list_all_folders(db))
    commands.add_command('list all queries', lambda: cmd_list_all_queries(c, db))
    commands.add_command('go to folder by id', lambda: cmd_go_to_folder_by_id(c, cache))
    commands.add_command('delete folder by id', lambda: cmd_delete_folder_by_id(c, db, cache))
    commands.add_command('add card', lambda: cmd_add_card(c, db, cache))
    commands.add_command('add query', lambda: cmd_add_query(db))
    commands.add_command('edit card', lambda: cmd_edit_card_by_id(c, db, cache))
