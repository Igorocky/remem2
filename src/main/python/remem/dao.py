from sqlite3 import Connection

from remem.cache import Cache
from remem.constants import CardTypes
from remem.dtos import Card, Folder, CardTranslate


def get_last_id(con: Connection) -> int:
    return int(con.execute("""SELECT last_insert_rowid()""").fetchone()[0])


def insert_folder(con: Connection, folder: Folder) -> int:
    con.execute(
        """insert into FOLDER(parent_id, name) values (:parent_id, :name)""",
        {'parent_id': folder.parent_id, 'name': folder.name})
    return get_last_id(con)


def select_folder(con: Connection, folder_id: int) -> Folder:
    parent_id, name = con.execute("""select parent_id, name from FOLDER where id = :id""",
                                  {'id': folder_id}).fetchone()
    return Folder(id=folder_id, parent_id=parent_id, name=name)


def select_folder_path(con: Connection, folder_id: int) -> list[Folder]:
    cur = con.execute("""
            with recursive folders(id, name, parent_id) as (
                select id, name, parent_id from FOLDER where id = :folder_id
                union all
                select pr.id, pr.name, pr.parent_id
                from folders ch inner join FOLDER pr on ch.parent_id = pr.id
            )
            select * from folders
        """, {'folder_id': folder_id})
    path = [Folder(id=f[0], name=f[1], parent_id=f[2]) for f in cur]
    path.reverse()
    return path


def update_folder(con: Connection, folder: Folder) -> None:
    if folder.id in {p.id for p in select_folder_path(con, folder.parent_id)}:
        raise Exception(f'A folder cannot be a child of itself')

    con.execute(""" update FOLDER set parent_id = :parent_id, name = :name where id = :id """,
                {'parent_id': folder.parent_id, 'name': folder.name, 'id': folder.id})


def delete_folder(con: Connection, folder_id: int) -> None:
    con.execute("""delete from FOLDER where id = :id""", {'id': folder_id})


def insert_card(con: Connection, card: Card) -> int:
    con.execute(
        """insert into CARD(ext_id, folder_id, card_type_id) values (:ext_id, :folder_id, :card_type_id)""",
        {'ext_id': card.ext_id, 'folder_id': card.folder_id, 'card_type_id': card.card_type_id}
    )
    card_id = get_last_id(con)
    if isinstance(card, CardTranslate):
        con.execute(
            """ insert into CARD_TRAN(id, lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2)
            values (:id, :lang1_id, :read_only1, :text1, :tran1, :lang2_id, :read_only2, :text2, :tran2) """,
            {'id': card_id,
             'lang1_id': card.lang1_id,
             'read_only1': 1 if card.readonly1 else 0,
             'text1': card.text1,
             'tran1': card.tran1,
             'lang2_id': card.lang2_id,
             'read_only2': 1 if card.readonly2 else 0,
             'text2': card.text2,
             'tran2': card.tran2, })
    else:
        raise Exception(f'Unexpected type of card {card}')
    return card_id


def select_card(con: Connection, cache: Cache, card_id: int) -> Card:
    row = con.execute(
        """ select ext_id, folder_id, card_type_id, crt_time from CARD where id = :id """,
        {'id': card_id}
    ).fetchone()
    card = Card(id=card_id, ext_id=row['ext_id'], folder_id=row['folder_id'], card_type_id=row['card_type_id'],
                crt_time=row['crt_time'], )
    card_type_code = cache.card_types_is[card.card_type_id]
    match card_type_code:
        case CardTypes.translate:
            row = con.execute(
                """ select lang1_id, read_only1, text1, tran1, lang2_id, read_only2, text2, tran2  
                from CARD_TRAN where id = :id """,
                {'id': card_id}
            ).fetchone()
            return CardTranslate(
                id=card_id, ext_id=card.ext_id, folder_id=card.folder_id, card_type_id=card.card_type_id,
                crt_time=card.crt_time, lang1_id=row['lang1_id'], lang1_str=cache.lang_is[row['lang1_str']],
                readonly1=row['readonly1'] != 0, text1=row['text1'], tran1=row['tran1'], lang2_id=row['lang2_id'],
                lang2_str=cache.lang_is[row['lang2_str']], readonly2=row['readonly2'] != 0, text2=row['text2'],
                tran2=row['tran2'],
            )
