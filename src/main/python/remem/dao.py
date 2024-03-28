import sqlite3
from ctypes import windll
from dataclasses import dataclass, field
from typing import Tuple
from uuid import uuid4

from remem.commands import CollectionOfCommands
from remem.console import Console
from remem.database import Database
from remem.dtos import CardTranslate, CardFillGaps

import tkinter as tk
from tkinter import ttk

from remem.ui import render_card_add_view

windll.shcore.SetProcessDpiAwareness(1)


@dataclass
class Folder:
    id: int
    parent_id: int | None
    name: str


@dataclass
class Dao:
    cur_path: list[Folder] = field(default_factory=lambda: [])
    lang_is: dict[int, str] = field(default_factory=lambda: {})
    lang_si: dict[str, int] = field(default_factory=lambda: {})
    card_types_is: dict[int, str] = field(default_factory=lambda: {})
    card_types_si: dict[str, int] = field(default_factory=lambda: {})


def make_new_folder(dao: Dao, db: Database, c: Console) -> None:
    name = c.input("New folder name: ").strip()
    if name == '':
        c.error('Folder name must not be empty')
        return
    db.con.execute(
        f'insert into FOLDER(parent_id, name) values (:parent, :name)',
        {'parent': dao.cur_path[-1].id if len(dao.cur_path) > 0 else None, 'name': name}
    )
    c.success('A folder created')


def show_current_folder(dao: Dao, c: Console) -> None:
    print(c.mark_info('Current folder: '), end='')
    print('/' + '/'.join([f'{f.name}:{f.id}' for f in dao.cur_path]))


def list_all_folders(db: Database) -> None:
    for r in db.con.execute("""
        with recursive folders(level, id, name, parent) as (
            select 0, id, name, parent_id from FOLDER where parent_id is null
            union all
            select level+1, ch.id, ch.name, ch.parent_id
            from FOLDER ch inner join folders pr on pr.id = ch.parent_id
            order by 1 desc
        )
        select level, id, name from folders
    """):
        print(f'{"    " * r[0]}{r[2]}:{r[1]}')


def go_to_folder_by_id(dao: Dao, db: Database, c: Console) -> None:
    inp = c.input("id of the folder to go to: ").strip()
    if inp == '':
        dao.cur_path = []
    else:
        new_path_iter = db.con.execute("""
            with recursive folders(id, name, parent) as (
                select id, name, parent_id from FOLDER where id = :folder_id
                union all
                select pr.id, pr.name, pr.parent_id
                from FOLDER pr inner join folders ch on pr.id = ch.parent
            )
            select * from folders
        """, {'folder_id': int(inp)})
        dao.cur_path = [Folder(id=f[0], name=f[1], parent_id=f[2]) for f in new_path_iter]
        dao.cur_path.reverse()
    show_current_folder(dao, c)


def delete_folder_by_id(dao: Dao, db: Database, c: Console) -> None:
    folder_id = int(c.input("id of the folder to delete: ").strip())
    if db.con.execute('select count(1) from FOLDER where id = :folder_id', {'folder_id': folder_id}).fetchone()[0] == 0:
        c.error(f'The folder with id of {folder_id} does not exist.')
    else:
        db.con.execute('delete from FOLDER where id = :folder_id', {'folder_id': folder_id})
        c.success('The folder is deleted.')
        if len(dao.cur_path) > 0 and dao.cur_path[-1].id == folder_id:
            dao.cur_path.pop()
            show_current_folder(dao, c)


def insert_card(folder_id: int, card_type_id: int, tr: sqlite3.Connection) -> int:
    tr.execute(
        'insert into CARD(ext_id, folder_id, card_type_id) values (:ext_id, :folder_id, :card_type_id)',
        {'ext_id': str(uuid4()), 'folder_id': folder_id, 'card_type_id': card_type_id}
    )
    return tr.execute('SELECT last_insert_rowid()').fetchone()[0]  # type: ignore[no-any-return]


def insert_card_translate(folder_id: int, card: CardTranslate, db: Database, dao: Dao) -> Tuple[bool, str]:
    try:
        with db.transaction() as tr:
            card_id = insert_card(folder_id=folder_id, card_type_id=dao.card_types_si['translate'], tr=tr)
            tr.execute("""
                insert into CARD_TRAN(id, lang1_id, text1, tran1, lang2_id, text2, tran2)
                values (:id, :lang1, :text1, :tran1, :lang2, :text2, :tran2)
            """,
                       {'id': card_id,
                        'lang1': dao.lang_si[card.lang1], 'text1': card.text1, 'tran1': card.tran1,
                        'lang2': dao.lang_si[card.lang2], 'text2': card.text2, 'tran2': card.tran2, })
        return True, ''
    except Exception as ex:
        return False, str(ex)


def insert_card_fill(card: CardFillGaps, db: Database) -> Tuple[bool, str]:
    return True, ''


def add_card(dao: Dao, db: Database, c: Console) -> None:
    # if len(dao.cur_path) == 0:
    #     c.error('Cannot create a note in the root folder.')
    #     return
    root = tk.Tk()
    root.title('Add card')
    root_frame = ttk.Frame(root)
    root_frame.grid()
    render_card_add_view(
        parent=root_frame, langs=list(dao.lang_si),
        on_card_tr_save=lambda card: insert_card_translate(folder_id=1, card=card, db=db, dao=dao),
        on_card_fill_save=lambda card: insert_card_fill(card, db),
    ).grid()
    root.mainloop()


def add_dao_commands(commands: CollectionOfCommands, db: Database, c: Console) -> None:
    dao = Dao()
    for r in db.con.execute("select id, name from LANGUAGE"):
        id = r[0]
        name = r[1]
        dao.lang_si[name] = id
        dao.lang_is[id] = name
    for r in db.con.execute("select id, code from CARD_TYPE"):
        type_id = r[0]
        type_code = r[1]
        dao.card_types_si[type_code] = type_id
        dao.card_types_is[type_id] = type_code
    commands.add_command('make new folder', lambda: make_new_folder(dao, db, c))
    commands.add_command('show current folder', lambda: show_current_folder(dao, c))
    commands.add_command('list all folders', lambda: list_all_folders(db))
    commands.add_command('go to folder by id', lambda: go_to_folder_by_id(dao, db, c))
    commands.add_command('delete folder by id', lambda: delete_folder_by_id(dao, db, c))
    commands.add_command('add card', lambda: add_card(dao, db, c))
