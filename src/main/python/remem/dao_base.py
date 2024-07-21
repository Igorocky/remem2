from sqlite3 import Connection
from uuid import uuid4

from remem.common import values
from remem.dtos import Folder, CardTranslate, Query, AnyCard, BaseCard, CardFillGaps, Task, TaskHistRec, \
    TaskWithBaseCard, Language, FolderWithPathDto


def get_last_id(con: Connection) -> int:
    row = con.execute("""SELECT last_insert_rowid()""").fetchone()
    return int(values(row)[0])


def insert_folder(con: Connection, folder: Folder) -> int:
    con.execute("""insert into FOLDER(parent_id, name) values (:parent_id, :name)""", folder.__dict__)
    return get_last_id(con)


def select_folder(con: Connection, folder_id: int) -> Folder | None:
    row = con.execute("""select * from FOLDER where id = ?""", [folder_id]).fetchone()
    return None if row is None else Folder(**row)


def select_folder_path(con: Connection, folder_id: int | None) -> list[Folder]:
    cur = con.execute("""
            with recursive folders(id, name, parent_id) as (
                select id, name, parent_id from FOLDER where id = ?
                union all
                select pr.id, pr.name, pr.parent_id
                from folders ch inner join FOLDER pr on ch.parent_id = pr.id
            )
            select * from folders
        """, [folder_id])
    path = [Folder(**row) for row in cur]
    path.reverse()
    return path


def select_all_folders_recursively(con: Connection, root_folder_id: int | None) -> list[FolderWithPathDto]:
    query = f"""
        with recursive folders(id, path, is_hidden) as (
            select id, '/'||name as path, name like '.%' as is_hidden 
            from FOLDER 
            where {'parent_id is null' if root_folder_id is None else 'id = :root_folder_id'}
            union all
            select ch.id, pr.path||'/'||ch.name as path, pr.is_hidden or ch.name like '.%' as is_hidden
            from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            where ch.name not like '.%'
        )
        select id, path, is_hidden from folders
        order by path
    """
    return [FolderWithPathDto(**r) for r in con.execute(query, {'root_folder_id': root_folder_id})]


def update_folder(con: Connection, folder: Folder) -> None:
    if folder.id in {p.id for p in select_folder_path(con, folder.parent_id)}:
        raise Exception(f'A folder cannot be a child of itself')

    con.execute(""" update FOLDER set parent_id = :parent_id, name = :name where id = :id """, folder.__dict__)


def delete_folder(con: Connection, folder_id: int) -> None:
    con.execute("""delete from FOLDER where id = ?""", [folder_id])


def insert_query(con: Connection, query: Query) -> int:
    con.execute("""insert into QUERY(name, text) values (:name, :text)""", query.__dict__)
    return get_last_id(con)


def select_query(con: Connection, query_id: int) -> Query | None:
    row = con.execute("""select * from QUERY where id = ?""", [query_id]).fetchone()
    return None if row is None else Query(**row)


def select_all_queries(con: Connection) -> list[Query]:
    return [Query(**row) for row in con.execute('select * from QUERY order by name')]


def update_query(con: Connection, query: Query) -> None:
    con.execute(""" update QUERY set name = :name, text = :text where id = :id """, query.__dict__)


def delete_query(con: Connection, query_id: int) -> None:
    con.execute("""delete from QUERY where id = ?""", [query_id])


def update_card(con: Connection, card: AnyCard) -> None:
    if isinstance(card, CardTranslate):
        con.execute(
            """
                update CARD_TRAN set lang1_id = :lang1_id, read_only1 = :read_only1, text1 = :text1, 
                lang2_id = :lang2_id, read_only2 = :read_only2, text2 = :text2, notes = :notes
                where id = :id
            """,
            card.__dict__
        )
    elif isinstance(card, CardFillGaps):
        con.execute(
            """
                update CARD_FILL set lang_id = :lang_id, descr = :descr, text = :text, notes = :notes
                where id = :id
            """,
            card.__dict__
        )
    else:
        raise Exception(f'Unexpected card type: {card}')


def delete_card(con: Connection, card_id: int) -> None:
    con.execute("""delete from CARD where id = ?""", [card_id])


def select_tasks_by_ids(con: Connection, task_ids: list[int]) -> list[Task]:
    task_ids = list(set(task_ids))
    result = []
    step = 100
    for idx in range(0, len(task_ids), step):
        ids = task_ids[idx:idx + step]
        task_ids_condition = ' or '.join(['id = ?'] * len(ids))
        for r in con.execute(f"""select * from TASK where {task_ids_condition}""", ids):
            result.append(Task(**r))
    return result


def select_tasks_with_base_cards_by_ids(con: Connection, task_ids: list[int]) -> list[TaskWithBaseCard]:
    task_ids = list(set(task_ids))
    result = []
    step = 100
    for idx in range(0, len(task_ids), step):
        ids = task_ids[idx:idx + step]
        task_ids_condition = ' or '.join(['t.id = ?'] * len(ids))
        for r in con.execute(
                f"""
                    select 
                        c.id c_id,
                        c.ext_id c_ext_id,
                        c.folder_id c_folder_id,
                        c.card_type_id c_card_type_id,
                        c.crt_time c_crt_time,
                        t.id t_id,
                        t.card_id t_card_id,
                        t.task_type_id t_task_type_id 
                    from TASK t left join CARD c on c.id = t.card_id where {task_ids_condition}
                """, ids):
            result.append(TaskWithBaseCard(
                card=BaseCard(
                    id=r['c_id'],
                    ext_id=r['c_ext_id'],
                    folder_id=r['c_folder_id'],
                    card_type_id=r['c_card_type_id'],
                    crt_time=r['c_crt_time'],
                ),
                id=r['t_id'],
                card_id=r['t_card_id'],
                task_type_id=r['t_task_type_id'],
            ))
    return result


def insert_task_hist(con: Connection, task_hist: TaskHistRec) -> int:
    con.execute(
        """insert into main.TASK_HIST(task_id, mark, note) values (:task_id, :mark, :note)""",
        task_hist.__dict__
    )
    return get_last_id(con)


def select_task_hist(
        con: Connection,
        task_ids: list[int],
        max_num_of_records_per_task: int
) -> dict[int, list[TaskHistRec]]:
    task_ids = list(set(task_ids))
    result: dict[int, list[TaskHistRec]] = {}
    step = 100
    for idx in range(0, len(task_ids), step):
        ids = task_ids[idx:idx + step]
        task_ids_condition = ' or '.join(['task_id = ?'] * len(ids))
        for r in con.execute(
                f"""
                    select task_id, time, mark, note from (
                        select task_id, time, mark, note,
                            row_number() over (partition by task_id order by time desc) rn
                        from TASK_HIST
                        where {task_ids_condition}
                    )
                    where rn <= ?
                    order by task_id, rn
                """,
                ids + [max_num_of_records_per_task]
        ):
            task_id = r['task_id']
            if task_id not in result:
                result[task_id] = []
            result[task_id].append(TaskHistRec(**r))
    return result


def insert_language(con: Connection, lang: Language) -> int:
    if len(lang.ext_id) == 0:
        lang.ext_id = str(uuid4())
    con.execute("""insert into LANGUAGE(ext_id, name) values (:ext_id, :name)""", lang.__dict__)
    return get_last_id(con)


def select_language(con: Connection, lang_id: int) -> Language | None:
    row = con.execute("""select * from LANGUAGE where id = ?""", [lang_id]).fetchone()
    return None if row is None else Language(**row)


def select_all_languages(con: Connection) -> list[Language]:
    return [Language(**row) for row in con.execute('select * from LANGUAGE order by name')]


def update_language(con: Connection, lang: Language) -> None:
    con.execute(""" update LANGUAGE set name = :name, ext_id = :ext_id where id = :id """, lang.__dict__)


def delete_language(con: Connection, lang_id: int) -> None:
    con.execute("""delete from LANGUAGE where id = ?""", [lang_id])
