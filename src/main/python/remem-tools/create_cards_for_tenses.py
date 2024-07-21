import dataclasses

from remem.app_context import init_app_context
from remem.app_settings import AppSettings
from remem.dao import insert_card
from remem.dao_base import insert_folder
from remem.dtos import Folder, CardTranslate, BaseCard


def create_cards(
        db_file: str,
        content_file: str,
        root_folder_id: int,
) -> None:
    ctx = init_app_context(
        app_settings=dataclasses.replace(
            AppSettings(),
            database_file=db_file,
            database_schema_script_path='',
        )
    )

    with ctx.database.transaction() as con:
        with open(content_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line != '':
                    unit, page, num1, num2 = [int(s) for s in line.split(' ')]
                    folder = Folder(parent_id=root_folder_id, name=f'Unit_{str(unit).rjust(2, '0')}')
                    folder.id = insert_folder(con, folder)
                    for i in range(1, num1 + 1):
                        card = CardTranslate(
                            base=BaseCard(folder_id=folder.id),
                            lang1_id=2,
                            read_only1=1,
                            text1=f'strona {page} zdanie {i}',
                            lang2_id=1,
                            read_only2=1,
                            text2=f'page {page + 1} sentence {i}',
                        )
                        print(f'{card=}')
                        insert_card(con, ctx.cache, card)
                    for i in range(num1 + 1, num2 + 1):
                        card = CardTranslate(
                            base=BaseCard(folder_id=folder.id),
                            lang1_id=2,
                            read_only1=1,
                            text1=f'strona {page + 2} zdanie {i}',
                            lang2_id=1,
                            read_only2=1,
                            text2=f'page {page + 3} sentence {i}',
                        )
                        print(f'{card=}')
                        insert_card(con, ctx.cache, card)


def main() -> None:
    create_cards(
        db_file='',
        content_file='',
        root_folder_id=7
    )


if __name__ == '__main__':
    main()
