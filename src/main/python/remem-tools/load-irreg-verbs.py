import xml.etree.ElementTree as ET
from typing import Tuple

from remem.app_context import init_app_context
from remem.dao import insert_folder, insert_translate_card
from remem.dtos import Folder

tmp_dir_path = '../../../temp/'


def parse_words(file_path: str) -> list[Tuple[str, str, str, str]]:
    tree = ET.parse(file_path)
    root = tree.getroot()
    form1 = [elem.text for elem in root.findall(".//td[1]/span")]
    form2 = [elem.text for elem in root.findall(".//td[2]/span")]
    form3 = [elem.text for elem in root.findall(".//td[3]/span")]
    translations = [elem.text for elem in root.findall(".//td[4]/span")]
    return [(str(tr), str(f1), str(f2), str(f3)) for tr, f1, f2, f3 in zip(translations, form1, form2, form3)]


def fill_database(words: list[Tuple[str, str, str, str]]) -> None:
    ctx = init_app_context('../../../temp/remem-app-settings.toml')
    db, cache = ctx.database, ctx.cache
    irregular_verbs = 'irregular_verbs'
    irreg_verbs_folder_row = db.con.execute('select id from FOLDER where name = ?', [irregular_verbs]).fetchone()
    irreg_verbs_folder_id = None if irreg_verbs_folder_row is None else irreg_verbs_folder_row['id']
    if irreg_verbs_folder_id is None:
        english_folder_id = insert_folder(db.con, Folder(parent_id=None, name='English'))
        irreg_verbs_folder_id = insert_folder(db.con, Folder(parent_id=english_folder_id, name=irregular_verbs))
    for (native, f1, f2, f3) in words:
        with db.transaction() as tr:
            insert_translate_card(
                tr,
                cache,
                folder_id=irreg_verbs_folder_id,
                lang1_id=4,
                read_only1=1,
                text1=native,
                tran1='',
                lang2_id=1,
                read_only2=0,
                text2=f'{f1.strip()} {f2.strip()} {f3.strip()}',
                tran2='',
            )


def main() -> None:
    words = parse_words(r'../../../temp/irreg_verbs.xml')
    print(f'{words=}')
    # fill_database(words)


if __name__ == '__main__':
    main()
