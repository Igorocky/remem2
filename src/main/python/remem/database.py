import sqlite3
from pathlib import Path


class Database:
    latest_db_version = 1

    def __init__(self, file_path: str) -> None:
        db_file = Path(file_path)
        if not db_file.parent.exists():
            db_file.parent.mkdir(parents=True)
        self.con = sqlite3.connect(file_path,
                                   autocommit=True)  # type: ignore[call-arg]
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

    def _init_database(self) -> None:
        self.con.executescript(Path('src/main/resources/schema_v1.sql').read_text('utf-8'))
        self.con.execute('pragma user_version = 1')

    def _upgrade_database(self) -> None:
        pass
