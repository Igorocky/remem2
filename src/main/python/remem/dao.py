import tkinter as tk
from ctypes import windll
from sqlite3 import Connection
from tkinter import ttk
from uuid import uuid4

from remem.cache import Cache
from remem.commands import CollectionOfCommands
from remem.common import Try, try_
from remem.console import Console
from remem.database import Database
from remem.dtos import CardTranslate, CardFillGaps, Card
from remem.ui import render_add_card_view

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


def cmd_go_to_folder_by_id(c: Console, db: Database, cache: Cache) -> None:
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


def insert_card_translate(db: Database, cache: Cache, card: CardTranslate) -> Try[None]:
    def do() -> None:
        set_generic_card_fields(cache, card)
        card.lang1_id = cache.lang_si[card.lang1_str]
        card.lang2_id = cache.lang_si[card.lang2_str]
        with db.transaction() as tr:
            card_id = insert_card(con=tr, card=card)
            card.id = card_id
            tr.execute("""
                insert into CARD_TRAN(id, lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2)
                values (:id, :lang1_id, :read_only1, :text1, :tran1, :lang2_id, :read_only2, :text2, :tran2)
            """,
                       {'id': card_id,
                        'lang1_id': card.lang1_id,
                        'read_only1': 1 if card.read_only1 else 0,
                        'text1': card.text1, 'tran1': card.tran1,
                        'lang2_id': card.lang2_id,
                        'read_only2': 1 if card.read_only2 else 0,
                        'text2': card.text2, 'tran2': card.tran2, })
            cache.card_tran_lang1_id = card.lang1_id
            cache.card_tran_lang2_id = card.lang2_id
            cache.card_tran_read_only1 = card.read_only1
            cache.card_tran_read_only2 = card.read_only2

    return try_(do)


def insert_card_fill(db: Database, cache: Cache, card: CardFillGaps) -> Try[None]:
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
        on_card_tr_save=lambda card: insert_card_translate(db=db, cache=cache, card=card),
        on_card_fill_save=lambda card: insert_card_fill(db=db, cache=cache, card=card),
        lang1_str=cache.lang_is[cache.card_tran_lang1_id],
        lang2_str=cache.lang_is[cache.card_tran_lang2_id],
        readonly1=cache.card_tran_read_only1,
        readonly2=cache.card_tran_read_only2,
    ).grid()
    root.mainloop()


def add_dao_commands(commands: CollectionOfCommands, db: Database, c: Console) -> None:
    cache = Cache(db)
    commands.add_command('make new folder', lambda: cmd_make_new_folder(c, db, cache))
    commands.add_command('show current folder', lambda: cmd_show_current_folder(c, cache))
    commands.add_command('list all folders', lambda: cmd_list_all_folders(db))
    commands.add_command('go to folder by id', lambda: cmd_go_to_folder_by_id(c, db, cache))
    commands.add_command('delete folder by id', lambda: cmd_delete_folder_by_id(c, db, cache))
    commands.add_command('add card', lambda: cmd_add_card(c, db, cache))
