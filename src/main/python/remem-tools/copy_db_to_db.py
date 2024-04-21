import sqlite3

from remem.common import enable_foreign_keys
from remem.database import dict_factory


def copy_cards_with_history(
        db_file_from: str,
        folder_id_from: int,
        db_file_to: str,
        folder_id_to: int,
) -> None:
    db_from = sqlite3.connect(db_file_from)
    db_from.row_factory = dict_factory
    enable_foreign_keys(db_from)

    db_to = sqlite3.connect(db_file_to, autocommit=True)
    db_to.row_factory = dict_factory
    enable_foreign_keys(db_to)

    cards = list(db_from.execute(
        """
        select 
            c.id as id, c.ext_id as ext_id, c.card_type_id as card_type_id, c.crt_time as crt_time,
            ct.lang1_id as lang1_id, ct.read_only1 as read_only1, ct.text1 as text1,
            ct.lang2_id as lang2_id, ct.read_only2 as read_only2, ct.text2 as text2 
        from CARD c inner join CARD_TRAN ct on c.id = ct.id
        where c.folder_id = ?
        """, [folder_id_from]
    ))
    for card in cards:
        db_to.execute(
            """
            insert into CARD (id, ext_id, folder_id, card_type_id, crt_time)
            values (:id, :ext_id, :folder_id, :card_type_id, :crt_time) 
            """, {**card, 'folder_id': folder_id_to}
        )
        db_to.execute(
            """
            insert into CARD_TRAN ( id, lang1_id, read_only1, text1, lang2_id, read_only2, text2, notes )
            values ( :id, :lang1_id, :read_only1, :text1, :lang2_id, :read_only2, :text2, :notes )
            """, {**card, 'notes': ''}
        )
        db_to.execute('delete from TASK where card_id = ?', [card['id']])
        for task in list(db_from.execute('select * from TASK where card_id = ?', [card['id']])):
            db_to.execute(
                """ insert into TASK (id, card_id, task_type_id) values (:id, :card_id, :task_type_id) """,
                task
            )
            for task_hist in list(db_from.execute('select * from TASK_HIST where task_id = ?', [task['id']])):
                db_to.execute(
                    """ insert into TASK_HIST (time, task_id, mark, note) values (:time, :task_id, :mark, :note) """,
                    task_hist
                )
    db_to.close()


def main():
    copy_cards_with_history(
        db_file_from='',
        folder_id_from=2,
        db_file_to='',
        folder_id_to=2
    )


if __name__ == '__main__':
    main()
