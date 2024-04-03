from remem.dao import select_folder_path
from remem.database import Database
from remem.dtos import Folder


class Cache:
    _sn_curr_folder = 'curr_folder'

    def __init__(self, db: Database):
        self._db = db
        self._cache: dict[str, str | None] = {}

        self.lang_si: dict[str, int] = {}
        self.lang_is: dict[int, str] = {}
        for r in db.con.execute("select id, name from LANGUAGE"):
            lang_id = r[0]
            lang_name = r[1]
            self.lang_si[lang_name] = lang_id
            self.lang_is[lang_id] = lang_name

        self.card_types_si: dict[str, int] = {}
        self.card_types_is: dict[int, str] = {}
        for r in db.con.execute("select id, code from CARD_TYPE"):
            type_id = r[0]
            type_code = r[1]
            self.card_types_si[type_code] = type_id
            self.card_types_is[type_id] = type_code

        self.task_types_si: dict[str, int] = {}
        self.task_types_is: dict[int, str] = {}
        for r in db.con.execute("select id, code from TASK_TYPE"):
            task_type_id = r[0]
            task_type_code = r[1]
            self.task_types_si[task_type_code] = task_type_id
            self.task_types_is[task_type_id] = task_type_code

        curr_folder_id = self._get_int(Cache._sn_curr_folder)
        self._cur_folder_path = [] if curr_folder_id is None else select_folder_path(self._db.con, curr_folder_id)

    def _read_value_from_db(self, key: str) -> str | None:
        for r in self._db.con.execute('select value from CACHE where key = :key', {'key': key}):
            value = str(r[0])
            return None if value == '' else value
        return None

    def _write_value_to_db(self, key: str, value: str | None) -> None:
        self._db.con.execute("""
            insert into CACHE(key,value) values (:key, :value)
            on conflict (key) do update set value = :value
            """, {'key': key, 'value': '' if value is None else value})

    def _get(self, key: str) -> str | None:
        if key not in self._cache:
            self._cache[key] = self._read_value_from_db(key)
        return self._cache[key]

    def _set(self, key: str, value: str | None) -> None:
        if self._get(key) != value:
            self._write_value_to_db(key, value)
            self._cache[key] = str(value)

    def _get_int(self, key: str) -> int | None:
        value = self._get(key)
        return int(value) if value is not None else None

    def _set_int(self, key: str, value: int | None) -> None:
        self._set(key, str(value) if value is not None else None)

    def get_curr_folder_path(self) -> list[Folder]:
        return self._cur_folder_path

    def set_curr_folder(self, folder_id: int | None) -> None:
        self._set_int(Cache._sn_curr_folder, folder_id)
        self._cur_folder_path = [] if folder_id is None else select_folder_path(self._db.con, folder_id)

    _sn_card_tran_lang1_id = 'card_tran_lang1_id'

    def get_card_tran_lang1_id(self) -> int:
        lang_id = self._get_int(Cache._sn_card_tran_lang1_id)
        return list(self.lang_is)[0] if lang_id is None else lang_id

    def set_card_tran_lang1_id(self, lang_id: int) -> None:
        self._set(Cache._sn_card_tran_lang1_id, str(lang_id))

    _sn_card_tran_lang2_id = 'card_tran_lang2_id'

    def get_card_tran_lang2_id(self) -> int:
        lang_id = self._get_int(Cache._sn_card_tran_lang2_id)
        return list(self.lang_is)[0] if lang_id is None else lang_id

    def set_card_tran_lang2_id(self, lang_id: int) -> None:
        self._set(Cache._sn_card_tran_lang2_id, str(lang_id))

    _sn_card_tran_read_only1 = 'card_tran_read_only1'

    def get_card_tran_read_only1(self) -> bool:
        return self._get_int(Cache._sn_card_tran_read_only1) == 1

    def set_card_tran_read_only1(self, read_only: bool) -> None:
        self._set(Cache._sn_card_tran_read_only1, '1' if read_only else '0')

    _sn_card_tran_read_only2 = 'card_tran_read_only2'

    def get_card_tran_read_only2(self) -> bool:
        return self._get_int(Cache._sn_card_tran_read_only2) == 1

    def set_card_tran_read_only2(self, read_only: bool) -> None:
        self._set(Cache._sn_card_tran_read_only2, '1' if read_only else '0')
