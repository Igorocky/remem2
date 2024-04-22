import sqlite3

from remem.common import enable_foreign_keys
from remem.database import dict_factory


def copy_examples_from_file_to_db(
        db_file: str,
        file_with_examples: str,
) -> None:
    db = sqlite3.connect(db_file, autocommit=True)  # type: ignore[call-arg]
    db.row_factory = dict_factory
    enable_foreign_keys(db)

    with open(file_with_examples, 'r', encoding='utf-8') as file:
        cnt = 0
        descr = None
        notes = None
        verb = None
        text = None
        for line in file:
            if line.startswith('d'):
                descr = line[1:].strip()
                notes = None
                verb = None
                text = None
            elif line.startswith('n'):
                notes = line[1:].strip()
                verb = None
                text = None
            elif line.startswith('v'):
                verb = line[1:].strip()
                text = None
            elif line.startswith('E'):
                if text is not None:
                    raise Exception(f'text is not None for {descr=} {notes=} duplicated text: {line[1:].strip()}')
                if verb is None:
                    raise Exception('verb is None')
                text = line[1:].strip()
                text = text.replace(verb, f'[[{verb}]]')
                print(f'{descr=} {notes=} {verb=} {text=}')
                db.execute(
                    f"""
                    update CARD_FILL set text = :text where text = '' and descr = :descr and notes = :notes
                    """, {'text': text, 'descr': descr, 'notes': notes}
                )
                cnt += 1
    print(f'{cnt=}')


def main() -> None:
    copy_examples_from_file_to_db(
        db_file='',
        file_with_examples=''
    )


if __name__ == '__main__':
    main()
