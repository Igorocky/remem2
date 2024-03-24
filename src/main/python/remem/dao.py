from dataclasses import dataclass, field

from remem.commands import CollectionOfCommands
from remem.console import Console
from remem.database import Database


@dataclass
class Folder:
    id: int
    parent_id: int | None
    name: str


@dataclass
class Dao:
    cur_path: list[Folder] = field(default_factory=lambda: [])


def make_new_folder(dao: Dao, db: Database, c: Console) -> None:
    name = c.input("New folder name: ").strip()
    if name == '':
        c.print_error('Folder name must not be empty')
        return
    db.con.execute(
        f'insert into FLD(parent, name) values (:parent, :name)',
        {'parent': dao.cur_path[-1].id if len(dao.cur_path) > 0 else None, 'name': name}
    )
    c.print_success('A folder created')


def show_current_folder(dao: Dao, c: Console) -> None:
    print(c.info('Current folder: '), end='')
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
        print(f'{"    "*r[0]}{r[2]}[{r[1]}]')


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
    show_current_folder(dao, c)


def add_dao_commands(commands: CollectionOfCommands, db: Database, c: Console) -> None:
    dao = Dao()
    commands.add_command('make new folder', lambda: make_new_folder(dao, db, c))
    commands.add_command('show current folder', lambda: show_current_folder(dao, c))
    commands.add_command('list all folders', lambda: list_all_folders(db))
    commands.add_command('go to folder by id', lambda: go_to_folder_by_id(dao, db, c))
