from remem.app_context import init_app_context
from remem.dao import insert_folder, insert_translate_card
from remem.dtos import Folder


def main() -> None:
    ctx = init_app_context('/temp/remem-app-settings.toml')
    db, cache = ctx.database, ctx.cache
    irregular_verbs = 'irregular_verbs'
    irreg_verbs_folder_row = db.con.execute('select id from FOLDER where name = ?', [irregular_verbs]).fetchone()
    irreg_verbs_folder_id = None if irreg_verbs_folder_row is None else irreg_verbs_folder_row['id']
    if irreg_verbs_folder_id is None:
        english_folder_id = insert_folder(db.con, Folder(parent_id=None, name='english'))
        irreg_verbs_folder_id = insert_folder(db.con, Folder(parent_id=english_folder_id, name=irregular_verbs))
    for w in ['a', 'b', 'c', 'd']:
        with db.transaction() as tr:
            insert_translate_card(
                tr,
                cache,
                folder_id=irreg_verbs_folder_id,
                lang1_id=4,
                read_only1=1,
                text1=w.upper(),
                tran1='',
                lang2_id=1,
                read_only2=0,
                text2=w.lower(),
                tran2='',
            )


if __name__ == '__main__':
    main()
