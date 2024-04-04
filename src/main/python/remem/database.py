import sqlite3
from pathlib import Path

from remem.appsettings import AppSettings
from remem.console import Console


class Transaction:
    def __init__(self, con: sqlite3.Connection, c: Console):
        self._con = con
        self._c = c

    def __enter__(self) -> sqlite3.Connection:
        if self._con.in_transaction:
            raise Exception('Internal error: cannot start a transaction.')
        self._con.autocommit = False
        return self._con

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore[no-untyped-def]
        try:
            if exc_type is not None:
                self._con.rollback()
                self._c.print_last_exception_info(exc_val)
                return False
            else:
                self._con.commit()
                return True
        finally:
            self._con.autocommit = True


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


class Database:
    latest_db_version = 1

    def __init__(self, app_settings: AppSettings, c: Console) -> None:
        self._c = c
        self._app_settings = app_settings
        self.con = sqlite3.connect(app_settings.database_file,
                                   autocommit=True)  # type: ignore[call-arg]
        self.con.row_factory = dict_factory
        self.con.execute('pragma foreign_keys = ON')
        foreign_keys = self.con.execute('pragma foreign_keys').fetchone()
        if list(foreign_keys.values())[0] != 1:
            raise Exception('Could not set foreign_keys = ON.')

        (db_ver,) = self.con.execute('pragma user_version').fetchone()
        if db_ver == 0:
            self._init_database()
        elif db_ver != Database.latest_db_version:
            self._upgrade_database()

        db_ver = self.con.execute('pragma user_version').fetchone()
        if list(db_ver.values())[0] != Database.latest_db_version:
            raise Exception('Could not init database.')

    def transaction(self) -> Transaction:
        return Transaction(self.con, self._c)

    def _init_database(self) -> None:
        self.con.executescript(Path(self._app_settings.database_schema_script_path).read_text('utf-8'))
        self.con.execute('pragma user_version = 1')

    def _upgrade_database(self) -> None:
        pass
