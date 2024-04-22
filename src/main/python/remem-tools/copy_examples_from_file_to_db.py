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
        form = None
        word = None
        example = None
        for line in file:
            if line.startswith('t'):
                descr = line[1:].strip()
                form = None
                word = None
                example = None
            elif line.startswith('f'):
                form = line[1:].strip()
                word = None
                example = None
            elif line.startswith('w'):
                word = line[1:].strip()
                example = None
            elif line.startswith('E'):
                if example is not None:
                    raise Exception(f'example is not None for {descr=} {form=} duplicated example: {line[1:].strip()}')
                if word is None:
                    raise Exception('word is None')
                example = line[1:].strip()
                example = example.replace(word, f'[[{word}]]')
                print(f'{descr=} {form=} {word=} {example=}')
                db.execute(
                    f"""
                    update CARD_FILL set text = :text where text = '' and descr = :descr and notes like '{form} %'
                    """, {'text': example, 'descr': descr}
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
