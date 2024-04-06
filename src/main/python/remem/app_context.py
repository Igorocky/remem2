from dataclasses import dataclass

from remem.cache import Cache
from remem.console import Console
from remem.database import Database


@dataclass
class AppCtx:
    console: Console
    database: Database
    cache: Cache