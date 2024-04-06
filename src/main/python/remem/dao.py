from sqlite3 import Connection

from remem.cache import Cache
from remem.common import values
from remem.constants import CardTypes
from remem.dtos import Folder, CardTranslate, Query, AnyCard, BaseCard


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


def insert_card(con: Connection, card: AnyCard) -> int:
    assert con.in_transaction
    con.execute(
        """insert into CARD(ext_id, folder_id, card_type_id) values (:ext_id, :folder_id, :card_type_id)""",
        card.base.__dict__
    )
    card_id = get_last_id(con)
    card.base.id = card_id
    card.id = card_id
    if isinstance(card, CardTranslate):
        con.execute(
            """ insert into CARD_TRAN(id, lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2)
            values (:id, :lang1_id, :read_only1, :text1, :tran1, :lang2_id, :read_only2, :text2, :tran2) """,
            card.__dict__
        )
    else:
        raise Exception(f'Unexpected type of card {card}')
    return card_id


def select_card(con: Connection, cache: Cache, card_id: int) -> AnyCard | None:
    row = con.execute('select * from CARD where id = ?', [card_id]).fetchone()
    if row is None:
        return None
    base_card = BaseCard(**row)
    card_type_code = cache.card_types_is[base_card.card_type_id]
    match card_type_code:
        case CardTypes.translate:
            row = con.execute(""" select * from CARD_TRAN where id = ? """, [card_id]).fetchone()
            return CardTranslate(base=base_card, **row)
        case _:
            raise Exception(f'Unexpected card type: {card_type_code}')


def update_card(con: Connection, card: AnyCard) -> None:
    if isinstance(card, CardTranslate):
        con.execute(
            """
                update CARD_TRAN set lang1_id = :lang1_id, read_only1 = :read_only1, text1 = :text1, tran1 = :tran1, 
                lang2_id = :lang2_id, read_only2 = :read_only2, text2 = :text2, tran2 = :tran2
                where id = :id
            """,
            card.__dict__
        )
    else:
        raise Exception(f'Unexpected card type: {card}')


def delete_card(con: Connection, card_id: int) -> None:
    con.execute("""delete from CARD where id = ?""", [card_id])
