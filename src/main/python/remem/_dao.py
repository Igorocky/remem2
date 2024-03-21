import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from remem.commands import Command


@dataclass
class RegisteredDatabase:
    name: Optional[str]
    path: str


class ListRegisteredDatabases(Command):
    def get_name(self) -> str:
        return 'listdbs'

    def get_description(self) -> str:
        return 'List registered databases'

    def run(self, user_input: str) -> None:
        file = Path('registered_databases.json')
        if file.is_file():
            text = file.read_text('utf-8')
            conf: list[dict] = json.loads(text)  # type: ignore[type-arg]
            dbs = [RegisteredDatabase(**c) for c in conf]
            for db in dbs:
                print(db)
        else:
            print('There are no registered databases.')


def _list_registered_databases() -> None:
    print('Hello from priv')
