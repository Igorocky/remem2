from dataclasses import dataclass

from remem.cache import Cache
from remem.console import Console
from remem.database import Database


@dataclass
class AppCtx:
    c: Console
    db: Database
    cache: Cache