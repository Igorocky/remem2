import tkinter as tk
from tkinter import ttk
from ctypes import windll
from dataclasses import dataclass, field
from typing import Tuple

from remem.commands import CollectionOfCommands
from remem.console import Console
from remem.database import Database
from remem.dtos import CardTranslate, CardFillGaps
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


def make_new_folder(dao: Dao, db: Database, c: Console) -> None:
    name = c.input("New folder name: ").strip()
    if name == '':
        c.error('Folder name must not be empty')
        return
    db.con.execute(
        f'insert into FLD(parent, name) values (:parent, :name)',
        {'parent': dao.cur_path[-1].id if len(dao.cur_path) > 0 else None, 'name': name}
    )
    c.success('A folder created')


def show_current_folder(dao: Dao, c: Console) -> None:
    print(c.mark_info('Current folder: '), end='')
    print('/' + '/'.join([f'{f.name}[{f.id}]' for f in dao.cur_path]))


def list_all_folders(db: Database) -> None:
    for r in db.con.execute("""
        with recursive folders(level, id, name, parent) as (
            select 0, id, name, parent from fld where parent is null
            union all
            select level+1, ch.id, ch.name, ch.parent
            from fld ch inner join folders pr on pr.id = ch.parent
            order by 1 desc
        )
        select level, id, name from folders
    """):
        print(f'{"    " * r[0]}{r[2]}[{r[1]}]')


def go_to_folder_by_id(dao: Dao, db: Database, c: Console) -> None:
    inp = c.input("id of the folder to go to: ").strip()
    if inp == '':
        dao.cur_path = []
    else:
        new_path_iter = db.con.execute("""
            with recursive folders(id, name, parent) as (
                select id, name, parent from fld where id = :folder_id
                union all
                select pr.id, pr.name, pr.parent
                from fld pr inner join folders ch on pr.id = ch.parent
            )
            select * from folders
        """, {'folder_id': int(inp)})
        dao.cur_path = [Folder(id=f[0], name=f[1], parent_id=f[2]) for f in new_path_iter]
        dao.cur_path.reverse()
    show_current_folder(dao, c)


def delete_folder_by_id(dao: Dao, db: Database, c: Console) -> None:
    folder_id = int(c.input("id of the folder to delete: ").strip())
    if db.con.execute('select count(1) from fld where id = :folder_id', {'folder_id': folder_id}).fetchone()[0] == 0:
        c.error(f'The folder with id of {folder_id} does not exist.')
    else:
        db.con.execute('delete from fld where id = :folder_id', {'folder_id': folder_id})
        c.success('The folder is deleted.')
        if len(dao.cur_path) > 0 and dao.cur_path[-1].id == folder_id:
            dao.cur_path.pop()
            show_current_folder(dao, c)


def save_card_translate(card: CardTranslate, db: Database) -> Tuple[bool, str]:
    return (True, '')


def save_card_fill(card: CardFillGaps, db: Database) -> Tuple[bool, str]:
    return (True, '')


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
        on_card_tr_save=lambda card: save_card_translate(card, db),
        on_card_fill_save=lambda card: save_card_fill(card, db),
    ).grid()
    root.mainloop()


def add_dao_commands(commands: CollectionOfCommands, db: Database, c: Console) -> None:
    dao = Dao()
    for r in db.con.execute("select id, name from LANG"):
        id = r[0]
        name = r[1]
        dao.lang_si[name] = id
        dao.lang_is[id] = name
    commands.add_command('make new folder', lambda: make_new_folder(dao, db, c))
    commands.add_command('show current folder', lambda: show_current_folder(dao, c))
    commands.add_command('list all folders', lambda: list_all_folders(db))
    commands.add_command('go to folder by id', lambda: go_to_folder_by_id(dao, db, c))
    commands.add_command('delete folder by id', lambda: delete_folder_by_id(dao, db, c))
    commands.add_command('add card', lambda: add_card(dao, db, c))
