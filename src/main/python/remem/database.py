import sqlite3
from pathlib import Path

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


class Database:
    latest_db_version = 1

    def __init__(self, file_path: str, c: Console) -> None:
        self._c = c
        self.con = sqlite3.connect(file_path,
                                   autocommit=True)  # type: ignore[call-arg]
        self.con.row_factory = sqlite3.Row
        self.con.execute('pragma foreign_keys = ON')
        (foreign_keys,) = self.con.execute('pragma foreign_keys').fetchone()
        if foreign_keys != 1:
            raise Exception('Could not set foreign_keys = ON.')

        (db_ver,) = self.con.execute('pragma user_version').fetchone()
        if db_ver == 0:
            self._init_database()
        elif db_ver != Database.latest_db_version:
            self._upgrade_database()

        (db_ver,) = self.con.execute('pragma user_version').fetchone()
        if db_ver != Database.latest_db_version:
            raise Exception('Could not init database.')

    def transaction(self) -> Transaction:
        return Transaction(self.con, self._c)

    def _init_database(self) -> None:
        self.con.executescript(Path('src/main/resources/schema_v1.sql').read_text('utf-8'))
        self.con.execute('pragma user_version = 1')

    def _upgrade_database(self) -> None:
        pass
