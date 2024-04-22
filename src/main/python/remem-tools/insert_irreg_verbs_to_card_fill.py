import dataclasses

from remem.app_context import init_app_context
from remem.app_settings import AppSettings
from remem.dao import insert_fill_gaps_card


def copy_cards_from_tran_to_fill(
        db_file: str,
        folder_id_from: int,
        folder_id_to: int,
) -> None:
    ctx = init_app_context(
        app_settings=dataclasses.replace(
            AppSettings(),
            database_file=db_file,
            database_schema_script_path='',
        )
    )
    for card in ctx.database.con.execute(
            """
            select ct.text1 as descr, ct.text2 as notes
            from CARD c left join CARD_TRAN ct on c.id = ct.id
            where c.folder_id = ?
            """, [folder_id_from]
    ):
        for i in range(3):
            with ctx.database.transaction() as tr:
                insert_fill_gaps_card(con=tr, cache=ctx.cache, folder_id=folder_id_to,
                                      lang_id=1,
                                      descr=card['descr'], text='', notes=f'{i + 1} {card['notes']}')


def main() -> None:
    copy_cards_from_tran_to_fill(
        db_file='',
        folder_id_from=2,
        folder_id_to=4
    )


if __name__ == '__main__':
    main()
