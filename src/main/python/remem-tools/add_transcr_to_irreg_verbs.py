import dataclasses

from remem.app_context import init_app_context
from remem.app_settings import AppSettings


def load_cards_to_file(
        db_file: str,
        folder_id: int,
        file_to_load_to: str,
) -> None:
    ctx = init_app_context(
        app_settings=dataclasses.replace(
            AppSettings(),
            database_file=db_file,
            database_schema_script_path='',
        )
    )

    file_text = []
    for r in ctx.database.con.execute(
        """
        select * from CARD_FILL cf inner join main.CARD C on C.id = cf.id
        where c.folder_id = ?
        """, [folder_id]
    ):
        notes:str = r['notes']
        note_parts = notes.split(' ')
        if len(note_parts) == 4 and note_parts[1][:1] != '/':
            word = note_parts[int(note_parts[0])]
            url = 'https://showmeword.com/definition/english_word/{word}'.replace('{word}', word)
            file_text.append(f'i\t{r["id"]}')
            file_text.append(f'd\t{r["descr"]}')
            file_text.append(f'n\t{r["notes"]}')
            file_text.append(f'u\t{url}')
            file_text.append(f't\t')
            file_text.append(f'')
            file_text.append(f'')
    with open(file_to_load_to, 'w', encoding='utf-8') as file:
        file.write('\n'.join(file_text))


def load_cards_to_db(
        db_file: str,
        file_to_load_from: str,
) -> None:
    ctx = init_app_context(
        app_settings=dataclasses.replace(
            AppSettings(),
            database_file=db_file,
            database_schema_script_path='',
        )
    )
    with open(file_to_load_from, 'r', encoding='utf-8') as file:
        card_id = None
        note = None
        for line in file:
            if line.startswith('i'):
                card_id = int(line[1:].strip())
            elif line.startswith('n'):
                note = line[1:].strip()
            elif line.startswith('t') and card_id is not None and note is not None:
                transcr = line[1:].strip().replace('|', '/')
                if len(transcr) == 0:
                    continue
                note_parts = note.split(' ')
                new_note = f'{note_parts[0]} {transcr}'
                print(f'{card_id=}')
                print(f'{new_note=}')
                print()
                ctx.database.con.execute(
                    f"""
                    update CARD_FILL set notes = :new_note where id = :card_id
                    """, {'new_note': new_note, 'card_id': card_id}
                )


def main() -> None:
    load_cards_to_file(
        db_file="",
        folder_id=3,
        file_to_load_to=""
    )
    # load_cards_to_db(
    #     db_file="",
    #     file_to_load_from=""
    # )


if __name__ == '__main__':
    main()
