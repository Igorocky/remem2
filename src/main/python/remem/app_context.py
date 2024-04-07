from dataclasses import dataclass

from remem.app_settings import load_app_settings
from remem.cache import Cache
from remem.console import Console
from remem.database import Database


@dataclass
class AppCtx:
    console: Console
    database: Database
    cache: Cache


def init_app_context(settings_path: str) -> AppCtx:
    app_settings = load_app_settings(settings_path)
    c = Console(app_settings=app_settings)
    database = Database(app_settings=app_settings, c=c)
    cache = Cache(database)
    return AppCtx(c, database, cache)
